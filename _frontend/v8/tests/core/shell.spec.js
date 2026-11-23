import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  ESTADOS_SIDEBAR,
  MODOS,
  aplicarSidebar,
  aplicarModo,
  iniciarShell,
  modoEmVigor
} from '~@/core/shell'

const html = document.documentElement
const SUFIXO_COOKIE = '; Path=/v8/; Max-Age=31536000; SameSite=Lax'

let parar = null
let gravacao = null

// Substitui o matchMedia do teste: largura da tela e modo do sistema.
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
function montarShell({ modo = null, sidebar = null, ariaModo = 'false', ariaSidebar = 'true' } = {}) {
  if (modo !== null) html.setAttribute('data-modo', modo)
  if (sidebar !== null) html.setAttribute('data-sidebar', sidebar)
  document.body.innerHTML = `
    <header>
      <button id="sidebar-1" type="button" data-v8-acao="sidebar" aria-expanded="${ariaSidebar}">
        <span id="sidebar-icone">menu</span>
      </button>
      <button id="modo-1" type="button" data-v8-acao="modo" aria-pressed="${ariaModo}">
        <span id="modo-icone">modo</span>
      </button>
    </header>
    <footer>
      <button id="sidebar-2" type="button" data-v8-acao="sidebar" aria-expanded="${ariaSidebar}">menu</button>
      <button id="modo-2" type="button" data-v8-acao="modo" aria-pressed="${ariaModo}">modo</button>
      <button id="outra" type="button" data-v8-acao="outra">outra</button>
      <button id="comum" type="button">comum</button>
    </footer>`
}

// O cabeçalho dos layouts com menu horizontal, como o Django o renderiza: botão do menu, dois
// grupos em <details> e, fora dele, uma sidebar com um grupo aberto. O tabindex existe só porque o
// DOM simulado não trata <summary> como focável.
function montarCabecalho({ aberto = true } = {}) {
  html.removeAttribute('data-modo')
  html.removeAttribute('data-sidebar')
  document.body.innerHTML = `
    <header class="v8-topbar">
      <button id="botao-menu" type="button" data-v8-acao="menu">
        <span id="botao-menu-icone">menu</span>
      </button>
      <nav id="v8-menu-principal" class="v8-menu">
        <ul>
          <li>
            <details id="grupo-1" class="v8-menu-grupo"${aberto ? ' open' : ''}>
              <summary id="rotulo-1" tabindex="0">Grupo 1</summary>
              <ul><li><button id="dentro-1" type="button">Filho 1</button></li></ul>
            </details>
          </li>
          <li>
            <details id="grupo-2" class="v8-menu-grupo">
              <summary id="rotulo-2" tabindex="0">Grupo 2</summary>
              <ul><li><button id="dentro-2" type="button">Filho 2</button></li></ul>
            </details>
          </li>
        </ul>
      </nav>
    </header>
    <aside class="v8-sidebar">
      <nav class="v8-menu"><details id="grupo-lateral" open><summary>Lateral</summary></details></nav>
    </aside>
    <main><p id="fora">fora</p></main>`
}

function grupo(id) {
  return document.getElementById(id)
}

function teclar(tecla) {
  document.dispatchEvent(new KeyboardEvent('keydown', { key: tecla, bubbles: true }))
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

  describe('menu do cabeçalho', () => {
    it('V8-SHELL-034: o botão do menu abre o menu como drawer e não grava cookie nem atributo', () => {
      ambiente({ telaLarga: false })
      montarCabecalho()
      const abrirMenuEstreito = vi.fn()
      iniciar({ abrirMenuEstreito })

      clicar('botao-menu-icone')

      expect(abrirMenuEstreito).toHaveBeenCalledTimes(1)
      expect(abrirMenuEstreito).toHaveBeenCalledWith(document.getElementById('botao-menu'))
      expect(cookiesGravados()).toEqual([])
      expect(html.hasAttribute('data-sidebar')).toBe(false)
    })

    it('V8-SHELL-034: sem abrirMenuEstreito o clique no botão do menu não faz nada', () => {
      ambiente({ telaLarga: false })
      montarCabecalho()
      iniciar()

      expect(() => clicar('botao-menu')).not.toThrow()

      expect(cookiesGravados()).toEqual([])
      expect(html.hasAttribute('data-sidebar')).toBe(false)
    })

    it('V8-SHELL-035: em tela larga o grupo que o servidor abriu começa fechado, só no cabeçalho', () => {
      ambiente({ telaLarga: true })
      montarCabecalho({ aberto: true })

      iniciar()

      expect(grupo('grupo-1').open).toBe(false)
      expect(grupo('grupo-lateral').open).toBe(true)
      expect(document.getElementById('v8-menu-principal').hasAttribute('data-v8-pronto')).toBe(true)
      expect(document.querySelector('.v8-sidebar .v8-menu').hasAttribute('data-v8-pronto')).toBe(false)
    })

    it('V8-SHELL-035: em tela estreita o grupo continua aberto, para o menu no drawer', () => {
      ambiente({ telaLarga: false })
      montarCabecalho({ aberto: true })

      iniciar()

      expect(grupo('grupo-1').open).toBe(true)
      expect(document.getElementById('v8-menu-principal').hasAttribute('data-v8-pronto')).toBe(true)
    })

    it('V8-SHELL-035: clique dentro do grupo o mantém aberto, e clique fora o fecha', () => {
      ambiente({ telaLarga: true })
      montarCabecalho()
      iniciar()
      grupo('grupo-1').open = true

      clicar('dentro-1')
      expect(grupo('grupo-1').open).toBe(true)

      clicar('fora')
      expect(grupo('grupo-1').open).toBe(false)
      // A sidebar não é do cabeçalho: os grupos dela não fecham.
      expect(grupo('grupo-lateral').open).toBe(true)
    })

    it('V8-SHELL-035: clicar em outro grupo fecha o que estava aberto', () => {
      ambiente({ telaLarga: true })
      montarCabecalho()
      iniciar()
      grupo('grupo-1').open = true

      clicar('dentro-2')

      expect(grupo('grupo-1').open).toBe(false)
    })

    it('V8-SHELL-035: ESC fecha o grupo aberto e devolve o foco ao rótulo dele', () => {
      ambiente({ telaLarga: true })
      montarCabecalho()
      iniciar()
      grupo('grupo-1').open = true
      document.getElementById('dentro-1').focus()

      teclar('Enter')
      expect(grupo('grupo-1').open).toBe(true)

      teclar('Escape')
      expect(grupo('grupo-1').open).toBe(false)
      expect(document.activeElement).toBe(document.getElementById('rotulo-1'))
      expect(grupo('grupo-lateral').open).toBe(true)
    })

    it('V8-SHELL-035: ESC sem grupo aberto não mexe no foco', () => {
      ambiente({ telaLarga: true })
      montarCabecalho({ aberto: false })
      iniciar()
      document.getElementById('botao-menu').focus()

      teclar('Escape')

      expect(document.activeElement).toBe(document.getElementById('botao-menu'))
      expect(grupo('grupo-lateral').open).toBe(true)
    })
  })

  describe('modo', () => {
    it('V8-SHELL-041: o botão alterna o modo, grava o cookie e informa o estado por aria-pressed', () => {
      ambiente()
      montarShell({ modo: 'claro' })
      iniciar()

      clicar('modo-1')

      expect(html.getAttribute('data-modo')).toBe('escuro')
      expect(cookiesGravados()).toEqual([`v8_modo=escuro${SUFIXO_COOKIE}`])
      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['true', 'true'])
      expect(modoEmVigor()).toBe('escuro')

      clicar('modo-icone')

      expect(html.getAttribute('data-modo')).toBe('claro')
      expect(cookiesGravados()).toEqual([
        `v8_modo=escuro${SUFIXO_COOKIE}`,
        `v8_modo=claro${SUFIXO_COOKIE}`
      ])
      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['false', 'false'])
    })

    it('V8-SHELL-041: sem data-modo o modo em vigor é o do sistema, e o clique parte dele', () => {
      ambiente({ sistemaEscuro: true })
      montarShell({ ariaModo: 'false' })

      expect(modoEmVigor()).toBe('escuro')

      iniciar()

      // O servidor não sabia do modo do sistema: o boot corrige o aria-pressed sem gravar nada.
      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['true', 'true'])
      expect(html.hasAttribute('data-modo')).toBe(false)
      expect(cookiesGravados()).toEqual([])

      clicar('modo-2')

      expect(html.getAttribute('data-modo')).toBe('claro')
      expect(cookiesGravados()).toEqual([`v8_modo=claro${SUFIXO_COOKIE}`])
      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['false', 'false'])
    })

    it('V8-SHELL-041: sem data-modo e com o sistema claro, o clique leva ao escuro', () => {
      ambiente({ sistemaEscuro: false })
      montarShell({ ariaModo: 'true' })
      iniciar()

      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['false', 'false'])

      clicar('modo-1')

      expect(html.getAttribute('data-modo')).toBe('escuro')
    })

    it('V8-SHELL-041: o meta theme-color recebe o valor de --cor-barra-navegador do modo', () => {
      ambiente()
      const estilo = document.createElement('style')
      estilo.textContent = `
        :root { --cor-barra-navegador: #fafafa; }
        [data-modo="escuro"] { --cor-barra-navegador: #101418; }`
      document.head.appendChild(estilo)
      const meta = document.createElement('meta')
      meta.name = 'theme-color'
      meta.content = '#fafafa'
      document.head.appendChild(meta)
      montarShell({ modo: 'claro' })
      iniciar()

      clicar('modo-1')
      expect(meta.getAttribute('content')).toBe('#101418')

      clicar('modo-1')
      expect(meta.getAttribute('content')).toBe('#fafafa')
    })

    it('V8-TEMA-025: ao iniciar, o meta theme-color recebe a cor da barra do tema em vigor', () => {
      ambiente()
      const estilo = document.createElement('style')
      estilo.textContent = `
        :root { --cor-barra-navegador: #114d81; }
        :root[data-tema="verde"] { --cor-barra-navegador: #0f6b4f; }
        :root[data-tema="verde"][data-modo="escuro"] { --cor-barra-navegador: #13211b; }`
      document.head.appendChild(estilo)
      const meta = document.createElement('meta')
      meta.name = 'theme-color'
      meta.content = '#114d81'
      document.head.appendChild(meta)
      montarShell({ modo: 'claro' })
      html.setAttribute('data-tema', 'verde')

      iniciar()
      expect(meta.getAttribute('content')).toBe('#0f6b4f')

      // Trocar o modo não muda o tema (V8-TEMA-001), e a cor segue os dois.
      clicar('modo-1')
      expect(html.getAttribute('data-tema')).toBe('verde')
      expect(meta.getAttribute('content')).toBe('#13211b')
      html.removeAttribute('data-tema')
      estilo.remove()
      meta.remove()
    })

    it('V8-SHELL-041: sem o token --cor-barra-navegador o meta theme-color não muda', () => {
      ambiente()
      const meta = document.createElement('meta')
      meta.name = 'theme-color'
      meta.content = '#abcdef'
      document.head.appendChild(meta)
      montarShell({ modo: 'claro' })
      iniciar()

      clicar('modo-1')

      expect(html.getAttribute('data-modo')).toBe('escuro')
      expect(meta.getAttribute('content')).toBe('#abcdef')
    })
  })

  describe('ouvinte', () => {
    it('V8-SHELL-031: há um ouvinte de clique e um de teclado, e a função devolvida os remove', () => {
      ambiente({ telaLarga: true })
      montarShell({ modo: 'claro', sidebar: 'expandida' })
      const instalar = vi.spyOn(document, 'addEventListener')
      const retirar = vi.spyOn(document, 'removeEventListener')

      const remover = iniciar()

      expect(instalar.mock.calls.map(chamada => chamada[0])).toEqual(['click', 'keydown'])

      remover()
      expect(retirar.mock.calls.map(chamada => chamada[0])).toEqual(['click', 'keydown'])
      clicar('sidebar-1')
      clicar('modo-1')

      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(html.getAttribute('data-modo')).toBe('claro')
      expect(cookiesGravados()).toEqual([])
    })

    it('V8-SHELL-041: clique fora dos botões ou em ação desconhecida não altera nada', () => {
      ambiente({ telaLarga: true })
      montarShell({ modo: 'claro', sidebar: 'expandida' })
      const abrirMenuEstreito = vi.fn()
      iniciar({ abrirMenuEstreito })

      clicar('outra')
      clicar('comum')
      document.body.click()

      expect(html.getAttribute('data-modo')).toBe('claro')
      expect(html.getAttribute('data-sidebar')).toBe('expandida')
      expect(cookiesGravados()).toEqual([])
      expect(abrirMenuEstreito).not.toHaveBeenCalled()
    })
  })

  describe('valores válidos', () => {
    it.each(['roxo', '', 'ESCURO', 'escuro; Path=/', '<script>', null, undefined, 1])(
      'V8-SHELL-052: aplicarModo recusa valor fora da lista (%s)',
      valor => {
        montarShell({ modo: 'claro' })

        expect(aplicarModo(valor)).toBe(false)

        expect(html.getAttribute('data-modo')).toBe('claro')
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
      montarShell({ modo: 'roxo"><script>', sidebar: 'aberta' })
      iniciar()

      // Atributo fora da lista vale como ausente: segue o sistema e o padrão.
      expect(modoEmVigor()).toBe('escuro')
      expect(atributos('[data-v8-acao="modo"]', 'aria-pressed')).toEqual(['true', 'true'])

      clicar('modo-1')
      clicar('sidebar-1')

      expect(html.getAttribute('data-modo')).toBe('claro')
      expect(html.getAttribute('data-sidebar')).toBe('recolhida')
      expect(cookiesGravados()).toEqual([
        `v8_modo=claro${SUFIXO_COOKIE}`,
        `v8_sidebar=recolhida${SUFIXO_COOKIE}`
      ])
    })

    it('V8-SHELL-052: qualquer sequência de cliques só grava valores da lista', () => {
      ambiente({ telaLarga: true })
      montarShell()
      iniciar()

      for (let i = 0; i < 5; i += 1) {
        clicar('modo-1')
        clicar('sidebar-2')
      }

      const gravados = cookiesGravados().map(cookie => cookie.split(';')[0].split('='))
      expect(gravados).toHaveLength(10)
      gravados.forEach(([nome, valor]) => {
        expect(['v8_modo', 'v8_sidebar']).toContain(nome)
        expect(nome === 'v8_modo' ? MODOS : ESTADOS_SIDEBAR).toContain(valor)
      })
      expect(MODOS).toEqual(['claro', 'escuro'])
      expect(ESTADOS_SIDEBAR).toEqual(['expandida', 'recolhida'])
    })
  })
})
