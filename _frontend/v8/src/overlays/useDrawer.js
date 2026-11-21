import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { abrirPainel } from '~@/overlays/urlSync'

// API de drawers (V8-OVL-030 a 054). Funciona dentro e fora de componentes.
//
//   const { openDrawer, openPanel } = useDrawer()
//   openDrawer({ componente: () => import('./Ajuda.vue'), props }, { side: 'left', size: 'sm' })
//   openDrawer({ frag: 'demo/cliente/7/historico' })
//   openDrawer({ el: 'demo-filtros' }, { side: 'left', mode: 'docked', modeEstreito: 'overlay' })
//   openPanel('cliente:7')   // fica em ?painel= e volta com o botão voltar
export function useDrawer() {
  const store = useOverlayStore(pinia)
  return {
    openDrawer: (conteudo, opcoes = {}) => store.openDrawer(conteudo, opcoes),
    openPanel: (valor, opcoes = {}) => abrirPainel(valor, opcoes)
  }
}
