import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import { abrirNovaAba, ir, recarregar } from '~@/core/navegacao'
import pinia from '~@/core/pinia'
import ModalSessao from '~@/http/ModalSessao.vue'
import { CHAVE_OVERLAY } from '~@/overlays/useOverlay'
import { useGlobalStore } from '~@/stores/GlobalStore'

import { assentar, chamadasPara, respostaJson, simularFetch } from './apoio'

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn(() => '/v8/demo/')
}))

const VERSAO_ANA = {
  is_authenticated: true,
  permissions: ['materia.add_materialegislativa'],
  user: { id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '' }
}

let controle = null
let montado = null
let versao = null
let fetch = null

function montar() {
  controle = { id: 'v8-overlay-1', close: vi.fn(), dismiss: vi.fn(), setDirty: vi.fn(), setTitle: vi.fn() }
  montado = mount(ModalSessao, {
    attachTo: document.body,
    global: { provide: { [CHAVE_OVERLAY]: controle } }
  })
  return montado
}

function botao(nome) {
  return montado.get(`[data-sessao="${nome}"]`)
}

function consultas() {
  return chamadasPara(fetch, '/api/version')
}

describe('ModalSessao', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useGlobalStore(pinia).$reset()
    versao = { version: 'v8' }
    fetch = simularFetch(() => respostaJson(versao))
  })

  afterEach(() => {
    montado?.unmount()
    montado = null
    vi.unstubAllGlobals()
  })

  it('V8-HTTP-022: explica a sessão expirada e oferece as três ações', () => {
    montar()
    expect(montado.text()).toContain('Sua sessão expirou')
    expect(botao('nova-aba').text()).toBe('Entrar em nova aba')
    expect(botao('ja-entrei').text()).toBe('Já entrei')
    expect(botao('ir-login').text()).toBe('Ir para o login')
    // Montar o modal não consulta nem fecha nada.
    expect(fetch).not.toHaveBeenCalled()
    expect(controle.close).not.toHaveBeenCalled()
  })

  it('V8-HTTP-022: "Entrar em nova aba" abre a tela /login/ com retorno para a base do v8', async () => {
    const global = useGlobalStore(pinia)
    global.urls.login = '/login/'
    global.urls.base = '/v8/'
    montar()
    await botao('nova-aba').trigger('click')
    expect(abrirNovaAba).toHaveBeenCalledTimes(1)
    expect(abrirNovaAba).toHaveBeenCalledWith('/login/?next=' + encodeURIComponent('/v8/'))
    // O modal continua aberto, e esta aba não sai do lugar.
    expect(controle.close).not.toHaveBeenCalled()
    expect(ir).not.toHaveBeenCalled()
    expect(recarregar).not.toHaveBeenCalled()
  })

  it('V8-HTTP-022: "Ir para o login" fecha o modal sem retomar', async () => {
    montar()
    await botao('ir-login').trigger('click')
    expect(controle.close).toHaveBeenCalledTimes(1)
    expect(controle.close).toHaveBeenCalledWith({ retomar: false })
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-HTTP-022: ao voltar o foco para a página, consulta /api/version e retoma se houver sessão', async () => {
    montar()
    versao = VERSAO_ANA
    window.dispatchEvent(new Event('focus'))
    await assentar()
    expect(consultas()).toHaveLength(1)
    expect(consultas()[0].init.method).toBe('GET')
    expect(controle.close).toHaveBeenCalledTimes(1)
    expect(controle.close).toHaveBeenCalledWith({ retomar: true, versao: VERSAO_ANA })
  })

  it('V8-HTTP-022: visibilitychange também consulta /api/version', async () => {
    montar()
    versao = VERSAO_ANA
    document.dispatchEvent(new Event('visibilitychange'))
    await assentar()
    expect(consultas()).toHaveLength(1)
    expect(controle.close).toHaveBeenCalledWith({ retomar: true, versao: VERSAO_ANA })
  })

  it('V8-HTTP-022: sem sessão, voltar o foco mantém o modal aberto e não avisa', async () => {
    montar()
    window.dispatchEvent(new Event('focus'))
    await assentar()
    expect(consultas()).toHaveLength(1)
    expect(controle.close).not.toHaveBeenCalled()
    expect(montado.find('[data-sessao="aviso"]').exists()).toBe(false)
  })

  it('V8-HTTP-022: "Já entrei" consulta /api/version e retoma se houver sessão', async () => {
    montar()
    versao = VERSAO_ANA
    await botao('ja-entrei').trigger('click')
    await assentar()
    expect(consultas()).toHaveLength(1)
    expect(controle.close).toHaveBeenCalledWith({ retomar: true, versao: VERSAO_ANA })
  })

  it('V8-HTTP-022: "Já entrei" sem sessão avisa e mantém o modal aberto', async () => {
    montar()
    await botao('ja-entrei').trigger('click')
    await assentar()
    expect(controle.close).not.toHaveBeenCalled()
    expect(montado.get('[data-sessao="aviso"]').text()).toContain('Ainda não há sessão aberta')
  })

  it('V8-HTTP-022: a consulta do modal não abre outro fluxo de sessão', async () => {
    fetch = simularFetch(() => respostaJson({ detail: 'Sem credenciais.' }, 401))
    montar()
    await botao('ja-entrei').trigger('click')
    await assentar()
    // Uma única chamada: o 401 de /api/version não gera nova consulta nem fecha o modal.
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(controle.close).not.toHaveBeenCalled()
    expect(montado.get('[data-sessao="aviso"]').text()).toContain('Não foi possível consultar o servidor')
  })

  it('V8-HTTP-022: fecha uma única vez, mesmo com foco e clique juntos', async () => {
    montar()
    versao = VERSAO_ANA
    window.dispatchEvent(new Event('focus'))
    document.dispatchEvent(new Event('visibilitychange'))
    await botao('ja-entrei').trigger('click')
    await assentar()
    window.dispatchEvent(new Event('focus'))
    await assentar()
    expect(consultas()).toHaveLength(1)
    expect(controle.close).toHaveBeenCalledTimes(1)
  })

  it('V8-HTTP-022: ao desmontar, deixa de ouvir o foco e a visibilidade', async () => {
    montar()
    montado.unmount()
    montado = null
    versao = VERSAO_ANA
    window.dispatchEvent(new Event('focus'))
    document.dispatchEvent(new Event('visibilitychange'))
    await assentar()
    expect(fetch).not.toHaveBeenCalled()
    expect(controle.close).not.toHaveBeenCalled()
  })

  it('V8-HTTP-043: o modal não tem campo de senha nem formulário', async () => {
    montar()
    await botao('ja-entrei').trigger('click')
    await assentar()
    expect(montado.findAll('input, textarea, select, form')).toHaveLength(0)
    expect(document.querySelectorAll('input[type="password"]')).toHaveLength(0)
    expect(montado.findAll('button')).toHaveLength(3)
  })

  it('V8-HTTP-043: nenhuma requisição do modal envia corpo', async () => {
    montar()
    versao = VERSAO_ANA
    await botao('nova-aba').trigger('click')
    await botao('ja-entrei').trigger('click')
    await assentar()
    expect(fetch.mock.calls.length).toBeGreaterThan(0)
    fetch.mock.calls.forEach(([, init]) => {
      expect(init.method).toBe('GET')
      expect(init.body).toBeUndefined()
    })
  })
})
