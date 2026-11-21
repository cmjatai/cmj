// Preparação comum dos testes: o que o jsdom não implementa e a limpeza entre testes.
import { afterEach, vi } from 'vitest'

if (!window.matchMedia) {
  window.matchMedia = query => ({
    matches: false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {}
  })
}

if (!window.ResizeObserver) {
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false
  Element.prototype.setPointerCapture = () => {}
  Element.prototype.releasePointerCapture = () => {}
}

afterEach(() => {
  document.body.innerHTML = ''
  document.head.querySelectorAll('script[type="application/json"]').forEach(el => el.remove())
  document.documentElement.removeAttribute('data-theme')
  document.documentElement.removeAttribute('data-sidebar')
  document.cookie.split(';').forEach(c => {
    const nome = c.split('=')[0].trim()
    if (nome) document.cookie = `${nome}=; Max-Age=0; Path=/`
    if (nome) document.cookie = `${nome}=; Max-Age=0; Path=/v8/`
  })
  vi.useRealTimers()
})
