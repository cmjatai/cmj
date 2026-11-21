// Apoio dos testes de overlay: monta o host da pilha num documento limpo.
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import pinia from '~@/core/pinia'
import OverlayHost from '~@/overlays/OverlayHost.vue'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useOverlay } from '~@/overlays/useOverlay'

export function novoStore() {
  const store = useOverlayStore(pinia)
  store.$limpar()
  return store
}

export function montarHost() {
  return mount(OverlayHost, { attachTo: document.body, global: { plugins: [pinia] } })
}

// Espera as importações sob demanda, as Promises e os quadros de animação.
export async function assentar(vezes = 3) {
  for (let i = 0; i < vezes; i += 1) {
    await flushPromises()
    await new Promise(resolver => setTimeout(resolver, 0))
  }
  await flushPromises()
}

// Componente de conteúdo que expõe o controle do overlay em que foi aberto.
export function conteudoDeTeste(controles = {}, marca = 'conteudo') {
  return defineComponent({
    props: { texto: { type: String, default: '' } },
    setup(props) {
      const overlay = useOverlay()
      controles[marca] = overlay
      return () => h('div', { 'data-teste': marca }, [
        h('button', { type: 'button', 'data-teste-botao': marca }, props.texto || marca)
      ])
    }
  })
}

export function dialogos() {
  return [...document.querySelectorAll('[data-overlay-id]')]
}

export function tecla(chave, alvo = document.activeElement || document.body) {
  alvo.dispatchEvent(new KeyboardEvent('keydown', { key: chave, bubbles: true, cancelable: true }))
}
