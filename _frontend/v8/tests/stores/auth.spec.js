import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '~@/stores/AuthStore'
import { ID_DADOS_GLOBAIS, useGlobalStore } from '~@/stores/GlobalStore'

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn(() => '/v8/')
}))

const GLOBAL_ANA = {
  autenticado: true,
  usuario: { id: 7, username: 'ana', nome: 'Ana Souza', avatar: '/media/ana.png' },
  permissoes: ['materia.add_materialegislativa', 'norma.view_normajuridica']
}

const ANONIMO = { is_authenticated: false, user: null, permissions: [] }

function escreverGlobal(texto) {
  const el = document.createElement('script')
  el.id = ID_DADOS_GLOBAIS
  el.type = 'application/json'
  el.textContent = texto
  document.body.appendChild(el)
}

function respostaJson(corpo, status = 200) {
  return new Response(JSON.stringify(corpo), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('AuthStore', () => {
  let fetch = null

  beforeEach(() => {
    setActivePinia(createPinia())
    fetch = vi.fn(async () => respostaJson({}))
    vi.stubGlobal('fetch', fetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('V8-ARQ-032: hidratar() preenche o store com os dados globais, sem requisição', () => {
    escreverGlobal(JSON.stringify(GLOBAL_ANA))
    const auth = useAuthStore()
    auth.hidratar()
    expect(auth.data_connect).toEqual({
      is_authenticated: true,
      user: { id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '/media/ana.png' },
      permissions: ['materia.add_materialegislativa', 'norma.view_normajuridica']
    })
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.permissions).toEqual(GLOBAL_ANA.permissoes)
    expect(auth.hasPermission('norma.view_normajuridica')).toBe(true)
    expect(auth.hasPermission('norma.add_normajuridica')).toBe(false)
    expect(auth.isVotante).toBe(false)
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-ARQ-032: o store já nasce preenchido quando os dados globais foram lidos antes', () => {
    escreverGlobal(JSON.stringify(GLOBAL_ANA))
    useGlobalStore().carregar()
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.data_connect.user).toEqual({ id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '/media/ana.png' })
    expect(auth.permissions).toEqual(GLOBAL_ANA.permissoes)
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-ARQ-032: nascer não lê #v8-global por conta própria', () => {
    escreverGlobal(JSON.stringify(GLOBAL_ANA))
    const auth = useAuthStore()
    expect(useGlobalStore().carregado).toBe(false)
    expect(auth.data_connect).toEqual(ANONIMO)
  })

  it('V8-ARQ-032: JSON ausente resulta em usuário anônimo, sem exceção', () => {
    const auth = useAuthStore()
    expect(() => auth.hidratar()).not.toThrow()
    expect(auth.data_connect).toEqual(ANONIMO)
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.isVotante).toBe(false)
    expect(auth.permissions).toEqual([])
    expect(auth.hasPermission('materia.add_materialegislativa')).toBe(false)
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-ARQ-032: JSON inválido resulta em usuário anônimo, sem exceção', () => {
    escreverGlobal('{ isto não é json')
    const auth = useAuthStore()
    expect(() => auth.hidratar()).not.toThrow()
    expect(auth.data_connect).toEqual(ANONIMO)
  })

  it('V8-ARQ-032: autenticado sem usuário é tratado como anônimo', () => {
    escreverGlobal(JSON.stringify({ autenticado: true, usuario: null, permissoes: ['x.y'] }))
    const auth = useAuthStore()
    auth.hidratar()
    expect(auth.data_connect).toEqual(ANONIMO)
  })

  it('V8-ARQ-032: as permissões do AuthStore são cópia, não a lista do GlobalStore', () => {
    escreverGlobal(JSON.stringify(GLOBAL_ANA))
    const auth = useAuthStore()
    auth.hidratar()
    auth.data_connect.permissions.push('base.add_tudo')
    expect(useGlobalStore().permissoes).toEqual(GLOBAL_ANA.permissoes)
  })

  it('V8-ARQ-032: dados de votante, quando vierem nos dados globais, são mantidos', () => {
    const votante = { parlamentar_id: 3, nome_parlamentar: 'Ana' }
    escreverGlobal(JSON.stringify({ ...GLOBAL_ANA, usuario: { ...GLOBAL_ANA.usuario, votante } }))
    const auth = useAuthStore()
    auth.hidratar()
    expect(auth.isVotante).toBe(true)
    expect(auth.data_connect.user.votante).toEqual(votante)
  })

  it('V8-HTTP-023: aplicarVersao() troca o estado pela resposta de /api/version', () => {
    const auth = useAuthStore()
    auth.aplicarVersao({
      name: 'PortalCMJ',
      version: 'v8',
      is_authenticated: true,
      permissions: ['a.b'],
      user: { id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '', votante: { parlamentar_id: 3 } }
    })
    expect(auth.data_connect).toEqual({
      is_authenticated: true,
      permissions: ['a.b'],
      user: { id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '', votante: { parlamentar_id: 3 } }
    })
    expect(auth.isVotante).toBe(true)
    auth.aplicarVersao({ name: 'PortalCMJ', version: 'v8' })
    expect(auth.data_connect).toEqual(ANONIMO)
    auth.aplicarVersao(null)
    expect(auth.data_connect).toEqual(ANONIMO)
  })

  it('V8-HTTP-030: loginStatus() consulta /api/version e devolve a resposta', async () => {
    const versao = { version: 'v8', is_authenticated: true, permissions: ['a.b'], user: { id: 7, username: 'ana', fullname: 'Ana', avatar: '' } }
    fetch.mockImplementation(async () => respostaJson(versao))
    const auth = useAuthStore()
    const dados = await auth.loginStatus()
    expect(dados).toEqual(versao)
    expect(new URL(fetch.mock.calls[0][0]).pathname).toBe('/api/version')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.permissions).toEqual(['a.b'])
  })

  it('V8-HTTP-030: logoutPortalCMJ() encerra a sessão e atualiza o estado', async () => {
    escreverGlobal(JSON.stringify(GLOBAL_ANA))
    fetch.mockImplementation(async url => (new URL(url).pathname === '/api/version'
      ? respostaJson({ version: 'v8' })
      : respostaJson({ detail: 'Desconexão efetuada com sucesso!' })))
    const auth = useAuthStore()
    auth.hidratar()
    const dados = await auth.logoutPortalCMJ()
    expect(dados).toEqual({ version: 'v8' })
    expect(fetch.mock.calls.map(([url, init]) => `${init.method} ${new URL(url).pathname}`)).toEqual([
      'DELETE /api/auth/session',
      'GET /api/version'
    ])
    expect(auth.data_connect).toEqual(ANONIMO)
  })

  it('V8-HTTP-043: o store não tem action de login por senha', () => {
    const auth = useAuthStore()
    expect(auth.loginPortalCMJ).toBeUndefined()
    expect(typeof auth.loginStatus).toBe('function')
    expect(typeof auth.logoutPortalCMJ).toBe('function')
  })
})
