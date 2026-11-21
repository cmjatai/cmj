import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  ESTADOS_SIDEBAR,
  TEMAS,
  aplicarSidebar,
  aplicarTema,
  iniciarShell,
  temaEmVigor
} from '~@/core/shell'

const html = document.documentElement
const SUFIXO_COOKIE = '; Path=/v8/; Max-Age=31536000; SameSite=Lax'

let parar = null
let gravacao = null

// Substitui o matchMedia do teste: largura da tela e tema do sistema.
function ambiente({ telaLarga = true, sistemaEscuro = false } = {}) {
  const respostas = {
    '(min-width: 64rem)': telaLarga,
    '(prefers-color-scheme: dark)': sistemaEscuro
  }
  vi.spyOn(window, 'matchMedia').mockImplementation(consulta => ({
    matches: respostas[consulta] ?? false,
    media: consulta,
    addEventListener: () => {},
    removeEventListener: () => {}
  }))
}

// O shell como o Django o renderiza: dois botões de cada ação, um deles com conteúdo interno.
function montarShell({ tema = null, sidebar = null, ariaTema = 'false', ariaSidebar = 'true' } = {}) {
  if (tema !== null) html.setAttribute('data-theme', tema)
  if (sidebar !== null) html.setAttribute('data-sidebar', sidebar)
  document.body.innerHTML = `
    <header>
      <button id="sidebar-1" type="button" data-v8-acao="sidebar" aria-expanded="${ariaSidebar}">
        <span id="sidebar-icone">menu</span>
      </button>
      <button id="tema-1" type="button" data-v8-acao="tema" aria-pressed="${ariaTema}">
        <span id="tema-icone">tema</span>
      </button>
    </header>
    <footer>
      <button id="sidebar-2" type="button" data-v8-acao="sidebar" aria-expanded="${ariaSidebar}">menu</button>
      <button id="tema-2" type="button" data-v8-acao="tema" aria-pressed="${ariaTema}">tema</button>
      <button id="outra" type="button" data-v8-acao="outra">outra</button>
      <button id="comum" type="button">comum</button>
    </footer>`
}

function iniciar(opcoes) {
  parar = iniciarShell(opcoes)
  return parar
}

function clicar(id) {
  document.getElementById(id).click()
}

function atributos(seletor, atributo) {
  return [...document.querySelectorAll(seletor)].map(el => el.getAttribute(atributo))
}

function cookiesGravados() {
  return gravacao.mock.calls.map(chamada => chamada[0])
}

function limparCookiesV8() {
  window.history.replaceState({}, '', '/v8/')
  document.cookie.split(';').forEach(c => {
    const nome = c.split('=')[0].trim()
    if (nome) document.cookie = `${nome}=; Max-Age=0; Path=/v8/`
  })
  window.history.replaceState({}, '', '/')
}

describe('shell', () => {
  beforeEach(() => {
    gravacao = vi.spyOn(document, 'cookie', 'set')
  })

  afterEach(() => {
    parar?.()
    parar = null
    document.head.querySelectorAll('meta[name="theme-color"], style').forEach(el => el.remove())
    limparCookiesV8()
  })

  describe('sidebar', () => {
    it('V8-SHELL-031: em tela larga o botão alterna o atributo, o cookie e o aria-expanded', () => {
      ambiente({ telaLarga: true })
      montarShell({ sidebar: 'expandida' })
      const abrirMenuEstreito = vi.fn()
      iniciar({ abrirMenuEstreito })

      clicar('sidebar-1')

      expect(html.getAttribute('data-sidebar')).toBe('recolhida')
      expect(cookiesGravados()).toEqual([`v8_sidebar=recolhida${SUFIXO_COOKIE}`])
      expect(atributos('[data-v8-acao="sidebar"]', 'aria-expanded')).toEqual(['false', 'false'])

      clicar('sidebar-2')

      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(cookiesGravados()).toEqual([
        `v8_sidebar=recolhida${SUFIXO_COOKIE}`,
        `v8_sidebar=expandida${SUFIXO_COOKIE}`
      ])
      expect(atributos('[data-v8-acao="sidebar"]', 'aria-expanded')).toEqual(['true', 'true'])
      expect(abrirMenuEstreito).not.toHaveBeenCalled()
    })

    it('V8-SHELL-031: sem data-sidebar vale expandida, e o clique recolhe', () => {
      ambiente({ telaLarga: true })
      montarShell()
      iniciar()

      clicar('sidebar-1')

      expect(html.getAttribute('data-sidebar')).toBe('recolhida')
      expect(cookiesGravados()).toEqual([`v8_sidebar=recolhida${SUFIXO_COOKIE}`])
    })

    it('V8-SHELL-031: o clique no conteúdo do botão vale como clique no botão', () => {
      ambiente({ telaLarga: true })
      montarShell({ sidebar: 'recolhida', ariaSidebar: 'false' })
      iniciar()

      clicar('sidebar-icone')

      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(atributos('[data-v8-acao="sidebar"]', 'aria-expanded')).toEqual(['true', 'true'])
    })

    it('V8-SHELL-031: o cookie gravado é lido de volta sob /v8/', async () => {
      const { lerCookie } = await import('~@/core/cookies')
      ambiente({ telaLarga: true })
      montarShell({ sidebar: 'expandida' })
      window.history.replaceState({}, '', '/v8/')
      iniciar()

      clicar('sidebar-1')

      expect(lerCookie('v8_sidebar')).toBe('recolhida')
    })

    it('V8-SHELL-032: em tela estreita o botão abre o menu e não altera cookie nem atributo', () => {
      ambiente({ telaLarga: false })
      montarShell({ sidebar: 'expandida' })
      const abrirMenuEstreito = vi.fn()
      iniciar({ abrirMenuEstreito })

      clicar('sidebar-icone')

      expect(abrirMenuEstreito).toHaveBeenCalledTimes(1)
      expect(abrirMenuEstreito).toHaveBeenCalledWith(document.getElementById('sidebar-1'))
      expect(cookiesGravados()).toEqual([])
      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(atributos('[data-v8-acao="sidebar"]', 'aria-expanded')).toEqual(['true', 'true'])
    })

    it('V8-SHELL-032: em tela estreita, sem abrirMenuEstreito, o clique não faz nada', () => {
      ambiente({ telaLarga: false })
      montarShell({ sidebar: 'recolhida', ariaSidebar: 'false' })
      iniciar()

      expect(() => clicar('sidebar-1')).not.toThrow()

      expect(cookiesGravados()).toEqual([])
      expect(html.getAttribute('data-sidebar')).toBe('recolhida')
    })
  })

  describe('tema', () => {
    it('V8-SHELL-041: o botão alterna o tema, grava o cookie e informa o estado por aria-pressed', () => {
      ambiente()
      montarShell({ tema: 'claro' })
      iniciar()

      clicar('tema-1')

      expect(html.getAttribute('data-theme')).toBe('escuro')
      expect(cookiesGravados()).toEqual([`v8_tema=escuro${SUFIXO_COOKIE}`])
      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['true', 'true'])
      expect(temaEmVigor()).toBe('escuro')

      clicar('tema-icone')

      expect(html.getAttribute('data-theme')).toBe('claro')
      expect(cookiesGravados()).toEqual([
        `v8_tema=escuro${SUFIXO_COOKIE}`,
        `v8_tema=claro${SUFIXO_COOKIE}`
      ])
      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['false', 'false'])
    })

    it('V8-SHELL-041: sem data-theme o tema em vigor é o do sistema, e o clique parte dele', () => {
      ambiente({ sistemaEscuro: true })
      montarShell({ ariaTema: 'false' })

      expect(temaEmVigor()).toBe('escuro')

      iniciar()

      // O servidor não sabia do tema do sistema: o boot corrige o aria-pressed sem gravar nada.
      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['true', 'true'])
      expect(html.hasAttribute('data-theme')).toBe(false)
      expect(cookiesGravados()).toEqual([])

      clicar('tema-2')

      expect(html.getAttribute('data-theme')).toBe('claro')
      expect(cookiesGravados()).toEqual([`v8_tema=claro${SUFIXO_COOKIE}`])
      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['false', 'false'])
    })

    it('V8-SHELL-041: sem data-theme e com o sistema claro, o clique leva ao escuro', () => {
      ambiente({ sistemaEscuro: false })
      montarShell({ ariaTema: 'true' })
      iniciar()

      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['false', 'false'])

      clicar('tema-1')

      expect(html.getAttribute('data-theme')).toBe('escuro')
    })

    it('V8-SHELL-041: o meta theme-color recebe o valor de --cor-barra-navegador do tema', () => {
      ambiente()
      const estilo = document.createElement('style')
      estilo.textContent = `
        :root { --cor-barra-navegador: #fafafa; }
        [data-theme="escuro"] { --cor-barra-navegador: #101418; }`
      document.head.appendChild(estilo)
      const meta = document.createElement('meta')
      meta.name = 'theme-color'
      meta.content = '#fafafa'
      document.head.appendChild(meta)
      montarShell({ tema: 'claro' })
      iniciar()

      clicar('tema-1')
      expect(meta.getAttribute('content')).toBe('#101418')

      clicar('tema-1')
      expect(meta.getAttribute('content')).toBe('#fafafa')
    })

    it('V8-SHELL-041: sem o token --cor-barra-navegador o meta theme-color não muda', () => {
      ambiente()
      const meta = document.createElement('meta')
      meta.name = 'theme-color'
      meta.content = '#abcdef'
      document.head.appendChild(meta)
      montarShell({ tema: 'claro' })
      iniciar()

      clicar('tema-1')

      expect(html.getAttribute('data-theme')).toBe('escuro')
      expect(meta.getAttribute('content')).toBe('#abcdef')
    })
  })

  describe('ouvinte', () => {
    it('V8-SHELL-031: há um único ouvinte de clique, e a função devolvida o remove', () => {
      ambiente({ telaLarga: true })
      montarShell({ tema: 'claro', sidebar: 'expandida' })
      const instalar = vi.spyOn(document, 'addEventListener')

      const remover = iniciar()

      expect(instalar).toHaveBeenCalledTimes(1)
      expect(instalar.mock.calls[0][0]).toBe('click')

      remover()
      clicar('sidebar-1')
      clicar('tema-1')

      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(html.getAttribute('data-theme')).toBe('claro')
      expect(cookiesGravados()).toEqual([])
    })

    it('V8-SHELL-041: clique fora dos botões ou em ação desconhecida não altera nada', () => {
      ambiente({ telaLarga: true })
      montarShell({ tema: 'claro', sidebar: 'expandida' })
      const abrirMenuEstreito = vi.fn()
      iniciar({ abrirMenuEstreito })

      clicar('outra')
      clicar('comum')
      document.body.click()

      expect(html.getAttribute('data-theme')).toBe('claro')
      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(cookiesGravados()).toEqual([])
      expect(abrirMenuEstreito).not.toHaveBeenCalled()
    })
  })

  describe('valores válidos', () => {
    it.each(['roxo', '', 'ESCURO', 'escuro; Path=/', '<script>', null, undefined, 1])(
      'V8-SHELL-052: aplicarTema recusa valor fora da lista (%s)',
      valor => {
        montarShell({ tema: 'claro' })

        expect(aplicarTema(valor)).toBe(false)

        expect(html.getAttribute('data-theme')).toBe('claro')
        expect(cookiesGravados()).toEqual([])
      }
    )

    it.each(['aberta', '', 'RECOLHIDA', 'recolhida; Path=/', '<script>', null, undefined, 0])(
      'V8-SHELL-052: aplicarSidebar recusa valor fora da lista (%s)',
      valor => {
        montarShell({ sidebar: 'expandida' })

        expect(aplicarSidebar(valor)).toBe(false)

        expect(html.getAttribute('data-sidebar')).toBe('expandida')
        expect(cookiesGravados()).toEqual([])
      }
    )

    it('V8-SHELL-052: atributo inválido no HTML é ignorado e nunca vai para o cookie', () => {
      ambiente({ telaLarga: true, sistemaEscuro: true })
      montarShell({ tema: 'roxo"><script>', sidebar: 'aberta' })
      iniciar()

      // Atributo fora da lista vale como ausente: segue o sistema e o padrão.
      expect(temaEmVigor()).toBe('escuro')
      expect(atributos('[data-v8-acao="tema"]', 'aria-pressed')).toEqual(['true', 'true'])

      clicar('tema-1')
      clicar('sidebar-1')

      expect(html.getAttribute('data-theme')).toBe('claro')
      expect(html.getAttribute('data-sidebar')).toBe('recolhida')
      expect(cookiesGravados()).toEqual([
        `v8_tema=claro${SUFIXO_COOKIE}`,
        `v8_sidebar=recolhida${SUFIXO_COOKIE}`
      ])
    })

    it('V8-SHELL-052: qualquer sequência de cliques só grava valores da lista', () => {
      ambiente({ telaLarga: true })
      montarShell()
      iniciar()

      for (let i = 0; i < 5; i += 1) {
        clicar('tema-1')
        clicar('sidebar-2')
      }

      const gravados = cookiesGravados().map(cookie => cookie.split(';')[0].split('='))
      expect(gravados).toHaveLength(10)
      gravados.forEach(([nome, valor]) => {
        expect(['v8_tema', 'v8_sidebar']).toContain(nome)
        expect(nome === 'v8_tema' ? TEMAS : ESTADOS_SIDEBAR).toContain(valor)
      })
      expect(TEMAS).toEqual(['claro', 'escuro'])
      expect(ESTADOS_SIDEBAR).toEqual(['expandida', 'recolhida'])
    })
  })
})
