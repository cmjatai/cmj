// Preparação comum dos testes: o que o jsdom não implementa e a limpeza entre testes.
import { afterEach, vi } from 'vitest'
import Vue from 'vue'
import { compileToFunctions } from 'vue-template-compiler'

Vue.config.productionTip = false
Vue.config.devtools = false

// `runtimeCompiler: true` do vue.config.js: o build usa o Vue completo, que compila o template
// de `template:` ou do HTML do elemento montado. Nos testes, as bibliotecas (vuex, bootstrap-vue,
// test-utils) carregam o Vue sem compilador, e uma segunda cópia do Vue quebraria os plugins.
// Por isso a compilação é acrescentada aqui à cópia única, como faz o build completo.
const montar = Vue.prototype.$mount
Vue.prototype.$mount = function (el, hydrating) {
  el = typeof el === 'string' ? document.querySelector(el) : el
  const options = this.$options
  if (!options.render) {
    let template = options.template
    if (typeof template === 'string' && template.charAt(0) === '#') {
      template = document.querySelector(template).innerHTML
    } else if (!template && el) {
      template = el.outerHTML
    }
    if (template) {
      const { render, staticRenderFns } = compileToFunctions(template, {
        delimiters: options.delimiters,
        comments: options.comments
      }, this)
      options.render = render
      options.staticRenderFns = staticRenderFns
    }
  }
  return montar.call(this, el, hydrating)
}

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

// Nenhum teste fala com a rede: quem precisar de HTTP usa o axios falso de tests/apoio.js.
const semRede = () => {
  throw new Error('Teste tentou usar a rede. Use o axios falso de tests/apoio.js.')
}
window.XMLHttpRequest.prototype.send = semRede
window.fetch = semRede
global.fetch = semRede
window.WebSocket = class {
  constructor () {
    semRede()
  }
}
global.WebSocket = window.WebSocket

afterEach(() => {
  document.body.innerHTML = ''
  window.localStorage.clear()
  vi.useRealTimers()
})
