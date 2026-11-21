import { inject } from 'vue'

// Chave pela qual cada overlay entrega seu controle ao conteúdo (V8-OVL-062).
export const CHAVE_OVERLAY = Symbol('v8-overlay')

const semOverlay = {
  id: null,
  close: () => {},
  dismiss: () => {},
  setDirty: () => {},
  setTitle: () => {}
}

// Dentro de um drawer ou modal devolve { id, close, dismiss, setDirty, setTitle }.
// Fora de um overlay devolve funções que não fazem nada.
export function useOverlay() {
  return inject(CHAVE_OVERLAY, semOverlay)
}
