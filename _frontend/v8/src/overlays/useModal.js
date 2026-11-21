import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'

// API de modals por Promise (V8-OVL-060 a 067). Funciona dentro e fora de componentes.
//
//   const { confirm, openModal, openForm, openWizard } = useModal()
//   const ok = await confirm({ titulo, mensagem, rotuloOk, variante: 'perigo' })
//   const dados = await openForm(() => import('./ClienteForm.vue'), { cliente })
export function useModal() {
  const store = useOverlayStore(pinia)
  return {
    confirm: opcoes => store.confirm(opcoes),
    openModal: (componente, props = {}, opcoes = {}) => store.openModal(componente, props, opcoes),
    openForm: (componente, props = {}, opcoes = {}) =>
      store.openModal(componente, props, { ...opcoes, type: 'form' }),
    openFullscreen: (componente, props = {}, opcoes = {}) =>
      store.openModal(componente, props, { ...opcoes, type: 'fullscreen' }),
    // opcoes: { passos, dados, concluir, title }
    openWizard: ({ passos, dados = {}, concluir = null, ...opcoes }) =>
      store.openModal(
        () => import('~@/overlays/ModalWizard.vue'),
        { passos, dadosIniciais: dados, concluir },
        { size: 'lg', ...opcoes, type: 'wizard' }
      )
  }
}
