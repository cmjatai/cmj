import { gravarCookieV8 } from '~@/core/cookies'

// Comportamentos do shell que o Django renderiza (docs/specs/v8/shell.md).
//
// O HTML já chega pronto: `<html data-tema>`, `data-modo` e `data-sidebar` vêm dos cookies, e os botões
// trazem `data-v8-acao`. Aqui há um ouvinte de clique e um de teclado no documento: eles trocam os
// atributos, gravam os cookies e fecham os grupos do menu do cabeçalho, sem recarregar a página.

export const MODOS = ['claro', 'escuro']
export const ESTADOS_SIDEBAR = ['expandida', 'recolhida']

const COOKIE_MODO = 'v8_modo'
const COOKIE_SIDEBAR = 'v8_sidebar'
const SELETOR_ACAO = '[data-v8-acao]'
const SELETOR_MODO = '[data-v8-acao="modo"]'
const SELETOR_SIDEBAR = '[data-v8-acao="sidebar"]'
const SELETOR_MENU_DO_CABECALHO = '.v8-topbar .v8-menu'
const SELETOR_GRUPO_ABERTO = '.v8-topbar .v8-menu details[open]'
const CONSULTA_ESCURO = '(prefers-color-scheme: dark)'
const CONSULTA_TELA_LARGA = '(min-width: 64rem)'
const TOKEN_BARRA_NAVEGADOR = '--cor-barra-navegador'

function marcar(seletor, atributo, valor) {
  document.querySelectorAll(seletor).forEach(botao => {
    botao.setAttribute(atributo, valor ? 'true' : 'false')
  })
}

// Modo em vigor: o do atributo ou, sem atributo válido, o do sistema (V8-SHELL-040).
export function modoEmVigor() {
  const atributo = document.documentElement.getAttribute('data-modo')
  if (MODOS.includes(atributo)) {
    return atributo
  }
  return window.matchMedia(CONSULTA_ESCURO).matches ? 'escuro' : 'claro'
}

function atualizarCorDaBarra() {
  const cor = window
    .getComputedStyle(document.documentElement)
    .getPropertyValue(TOKEN_BARRA_NAVEGADOR)
    .trim()
  if (!cor) {
    return
  }
  document.querySelectorAll('meta[name="theme-color"]').forEach(meta => {
    meta.setAttribute('content', cor)
  })
}

// Só `claro` e `escuro` chegam ao atributo e ao cookie (V8-SHELL-052).
export function aplicarModo(modo) {
  if (!MODOS.includes(modo)) {
    return false
  }
  document.documentElement.setAttribute('data-modo', modo)
  gravarCookieV8(COOKIE_MODO, modo)
  marcar(SELETOR_MODO, 'aria-pressed', modo === 'escuro')
  atualizarCorDaBarra()
  return true
}

export function sidebarEmVigor() {
  const atributo = document.documentElement.getAttribute('data-sidebar')
  return ESTADOS_SIDEBAR.includes(atributo) ? atributo : 'expandida'
}

// Só `expandida` e `recolhida` chegam ao atributo e ao cookie (V8-SHELL-052).
export function aplicarSidebar(estado) {
  if (!ESTADOS_SIDEBAR.includes(estado)) {
    return false
  }
  document.documentElement.setAttribute('data-sidebar', estado)
  gravarCookieV8(COOKIE_SIDEBAR, estado)
  marcar(SELETOR_SIDEBAR, 'aria-expanded', estado === 'expandida')
  return true
}

function alternarModo() {
  aplicarModo(modoEmVigor() === 'escuro' ? 'claro' : 'escuro')
}

function alternarSidebar(botao, abrirMenuEstreito) {
  if (window.matchMedia(CONSULTA_TELA_LARGA).matches) {
    aplicarSidebar(sidebarEmVigor() === 'expandida' ? 'recolhida' : 'expandida')
    return
  }
  // Em tela estreita o menu abre como drawer e o cookie não muda (V8-SHELL-032).
  if (typeof abrirMenuEstreito === 'function') {
    abrirMenuEstreito(botao)
  }
}

// Fecha os grupos abertos do menu do cabeçalho, menos o que contém `exceto` (V8-SHELL-035).
function fecharGruposDoCabecalho(exceto = null) {
  document.querySelectorAll(SELETOR_GRUPO_ABERTO).forEach(grupo => {
    if (!exceto || !grupo.contains(exceto)) {
      grupo.removeAttribute('open')
    }
  })
}

// O servidor abre o grupo do item ativo, que é o certo para a sidebar. No cabeçalho, em tela
// larga, ele começa fechado. O atributo avisa o CSS de que o menu já foi assumido (V8-SHELL-035).
function prepararMenuDoCabecalho() {
  const telaLarga = window.matchMedia(CONSULTA_TELA_LARGA).matches
  document.querySelectorAll(SELETOR_MENU_DO_CABECALHO).forEach(menu => {
    if (telaLarga) {
      menu.querySelectorAll('details[open]').forEach(grupo => grupo.removeAttribute('open'))
    }
    menu.setAttribute('data-v8-pronto', '')
  })
}

// Instala os ouvintes do shell, um de clique e um de teclado, e devolve a função que os remove.
export function iniciarShell({ abrirMenuEstreito } = {}) {
  function aoClicar(event) {
    fecharGruposDoCabecalho(event.target)
    const botao = event.target?.closest?.(SELETOR_ACAO)
    if (!botao) {
      return
    }
    const acao = botao.getAttribute('data-v8-acao')
    if (acao === 'modo') {
      event.preventDefault()
      alternarModo()
    } else if (acao === 'sidebar') {
      event.preventDefault()
      alternarSidebar(botao, abrirMenuEstreito)
    } else if (acao === 'menu') {
      // Layouts com o menu no cabeçalho: o botão só existe em tela estreita (V8-SHELL-034).
      event.preventDefault()
      if (typeof abrirMenuEstreito === 'function') {
        abrirMenuEstreito(botao)
      }
    }
  }

  function aoTeclar(event) {
    if (event.key !== 'Escape') {
      return
    }
    const abertos = [...document.querySelectorAll(SELETOR_GRUPO_ABERTO)]
    if (!abertos.length) {
      return
    }
    const comFoco = abertos.find(grupo => grupo.contains(document.activeElement))
    fecharGruposDoCabecalho()
    comFoco?.querySelector('summary')?.focus()
  }

  document.addEventListener('click', aoClicar)
  document.addEventListener('keydown', aoTeclar)
  prepararMenuDoCabecalho()

  // O servidor só conhece o cookie: sem ele, quem sabe o modo em vigor é o navegador.
  marcar(SELETOR_MODO, 'aria-pressed', modoEmVigor() === 'escuro')
  // O HTML traz a cor do oficial; o tema e o modo em vigor podem ter outra (V8-TEMA-025).
  atualizarCorDaBarra()

  return () => {
    document.removeEventListener('click', aoClicar)
    document.removeEventListener('keydown', aoTeclar)
  }
}

export default { iniciarShell, modoEmVigor, aplicarModo, sidebarEmVigor, aplicarSidebar }
