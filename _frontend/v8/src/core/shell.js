import { gravarCookieV8 } from '~@/core/cookies'

// Comportamentos do shell que o Django renderiza (docs/specs/v8/shell.md).
//
// O HTML já chega pronto: `<html data-theme>` e `<html data-sidebar>` vêm dos cookies, e os botões
// trazem `data-v8-acao`. Aqui só há um ouvinte de clique no documento, que troca os atributos e
// grava os cookies, sem recarregar a página.

export const TEMAS = ['claro', 'escuro']
export const ESTADOS_SIDEBAR = ['expandida', 'recolhida']

const COOKIE_TEMA = 'v8_tema'
const COOKIE_SIDEBAR = 'v8_sidebar'
const SELETOR_ACAO = '[data-v8-acao]'
const SELETOR_TEMA = '[data-v8-acao="tema"]'
const SELETOR_SIDEBAR = '[data-v8-acao="sidebar"]'
const CONSULTA_ESCURO = '(prefers-color-scheme: dark)'
const CONSULTA_TELA_LARGA = '(min-width: 64rem)'
const TOKEN_BARRA_NAVEGADOR = '--cor-barra-navegador'

function marcar(seletor, atributo, valor) {
  document.querySelectorAll(seletor).forEach(botao => {
    botao.setAttribute(atributo, valor ? 'true' : 'false')
  })
}

// Tema em vigor: o do atributo ou, sem atributo válido, o do sistema (V8-SHELL-040).
export function temaEmVigor() {
  const atributo = document.documentElement.getAttribute('data-theme')
  if (TEMAS.includes(atributo)) {
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
export function aplicarTema(tema) {
  if (!TEMAS.includes(tema)) {
    return false
  }
  document.documentElement.setAttribute('data-theme', tema)
  gravarCookieV8(COOKIE_TEMA, tema)
  marcar(SELETOR_TEMA, 'aria-pressed', tema === 'escuro')
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

function alternarTema() {
  aplicarTema(temaEmVigor() === 'escuro' ? 'claro' : 'escuro')
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

// Instala o único ouvinte de clique do shell e devolve a função que o remove.
export function iniciarShell({ abrirMenuEstreito } = {}) {
  function aoClicar(event) {
    const botao = event.target?.closest?.(SELETOR_ACAO)
    if (!botao) {
      return
    }
    const acao = botao.getAttribute('data-v8-acao')
    if (acao === 'tema') {
      event.preventDefault()
      alternarTema()
    } else if (acao === 'sidebar') {
      event.preventDefault()
      alternarSidebar(botao, abrirMenuEstreito)
    }
  }

  document.addEventListener('click', aoClicar)

  // O servidor só conhece o cookie: sem ele, quem sabe o tema em vigor é o navegador.
  marcar(SELETOR_TEMA, 'aria-pressed', temaEmVigor() === 'escuro')

  return () => document.removeEventListener('click', aoClicar)
}

export default { iniciarShell, temaEmVigor, aplicarTema, sidebarEmVigor, aplicarSidebar }
