import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useSyncStore } from '~@/stores/SyncStore'
import WebSocketManager from '~@/utils/ws/WebSocketManager'

const { conexoes } = vi.hoisted(() => ({ conexoes: [] }))

vi.mock('~@/utils/ws/WebSocketManager', () => ({
  default: vi.fn(class {
    constructor() {
      this.ouvintes = {}
      this.enviadas = []
      conexoes.push(this)
    }

    on(evento, funcao) {
      this.ouvintes[evento] = funcao
    }

    send(mensagem) {
      this.enviadas.push(mensagem)
    }
  })
}))

vi.mock('~@/utils/timer/TimerWorkerService', () => ({
  default: { startTimer: vi.fn(), stopTimer: vi.fn() }
}))

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn(() => '/v8/')
}))

function respostaJson(corpo) {
  return new Response(JSON.stringify(corpo), { status: 200, headers: { 'Content-Type': 'application/json' } })
}

describe('SyncStore', () => {
  let sync = null
  let fetch = null

  beforeEach(() => {
    conexoes.length = 0
    vi.mocked(WebSocketManager).mockClear()
    setActivePinia(createPinia())
    fetch = vi.fn(async () => respostaJson({ results: [{ id: 1, nome: 'a' }, { id: 2, nome: 'b' }] }))
    vi.stubGlobal('fetch', fetch)
    sync = useSyncStore()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('V8-ARQ-041: criar o store não abre o WebSocket', () => {
    expect(WebSocketManager).not.toHaveBeenCalled()
    expect(sync.wsManager).toBeNull()
    expect(sync.wsConnected).toBe(false)
  })

  it('V8-ARQ-041: ações que só mexem no cache local não abrem o WebSocket', () => {
    sync.invalidateDataCache(['materia'], ['materialegislativa'])
    sync.cleanInvalidatedDataCache('materia', 'materialegislativa')
    sync.invalidateCacheItems('materia', 'materialegislativa', [1])
    sync.DELETE_DATA_CACHE({ key: 'materia_materialegislativa', value: { id: 1 } })
    sync.stopLocalCronometro(1)
    sync.syncModels([])
    expect(WebSocketManager).not.toHaveBeenCalled()
  })

  it('V8-ARQ-041: fetchSync abre o WebSocket no primeiro uso e mantém o comportamento', async () => {
    const cache = await sync.fetchSync({ app: 'materia', model: 'materialegislativa', only_first_page: true })
    expect(WebSocketManager).toHaveBeenCalledTimes(1)
    expect(Object.keys(cache)).toEqual(['1', '2'])
    expect(sync.data_cache.materia_materialegislativa[2].nome).toBe('b')
    expect(sync.models.materia.materialegislativa).toBeTruthy()
    const url = new URL(fetch.mock.calls[0][0])
    expect(url.pathname).toBe('/api/materia/materialegislativa/')
    expect(url.searchParams.get('page')).toBe('1')
    expect(url.searchParams.get('o')).toBe('id')
  })

  it('V8-ARQ-041: a conexão é única, por mais ações que precisem dela', async () => {
    await sync.fetchSync({ app: 'materia', model: 'materialegislativa', only_first_page: true })
    await sync.fetchSync({ app: 'norma', model: 'normajuridica', only_first_page: true })
    sync.registerModels('sessao', ['sessaoplenaria'])
    sync.sendSyncMessage({ type: 'ping' })
    sync.startLocalCronometro(1)
    sync.syncModels([{ app: 'painelset', models: ['evento'] }])
    sync.initialize()
    expect(WebSocketManager).toHaveBeenCalledTimes(1)
    expect(conexoes).toHaveLength(1)
  })

  it('V8-ARQ-041: registerModels, sendSyncMessage, startLocalCronometro e syncModels também abrem a conexão', () => {
    const acoes = [
      store => store.registerModels('sessao', ['sessaoplenaria']),
      store => store.sendSyncMessage({ type: 'ping' }),
      store => store.startLocalCronometro(1),
      store => store.syncModels([{ app: 'painelset', models: ['evento'] }])
    ]
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    acoes.forEach(acao => {
      setActivePinia(createPinia())
      vi.mocked(WebSocketManager).mockClear()
      acao(useSyncStore())
      expect(WebSocketManager).toHaveBeenCalledTimes(1)
    })
  })

  it('V8-ARQ-041: os eventos do socket continuam atualizando o store', async () => {
    await sync.fetchSync({ app: 'materia', model: 'materialegislativa', only_first_page: true })
    const conexao = conexoes[0]
    conexao.ouvintes.connected()
    expect(sync.wsConnected).toBe(true)

    sync.sendSyncMessage({ type: 'ola' })
    expect(conexao.enviadas).toEqual([{ type: 'ola' }])

    conexao.ouvintes.message({ type: 'pong', server_time_diff: 12 })
    expect(sync.lastServerSync).toMatchObject({ type: 'pong', server_time_diff: 12 })

    conexao.ouvintes.message({
      type: 'sync_refresh.message',
      message: { app: 'materia', model: 'materialegislativa', id: 2, action: 'post_save', instance: { id: 2, nome: 'novo' }, timestamp: Date.now() + 1000 }
    })
    expect(sync.data_cache.materia_materialegislativa[2].nome).toBe('novo')

    conexao.ouvintes.disconnected()
    expect(sync.wsConnected).toBe(false)
  })

  it('V8-ARQ-041: mensagem enviada antes de o socket conectar segue sem envio, como antes', () => {
    const aviso = vi.spyOn(console, 'warn').mockImplementation(() => {})
    sync.sendSyncMessage({ type: 'ola' })
    expect(conexoes).toHaveLength(1)
    expect(conexoes[0].enviadas).toEqual([])
    expect(aviso).toHaveBeenCalledTimes(1)
  })
})
