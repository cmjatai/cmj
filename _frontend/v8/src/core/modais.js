// Registro de modals abertos por data-modal="<nome>:<argumento>" (V8-OVL-082).
export const modais = {
  'demo-resumo': {
    componente: () => import('~@/modules/demo/modais/ClienteResumo.vue'),
    props: arg => ({ id: Number(arg) }),
    opcoes: { type: 'fullscreen', title: 'Resumo do cliente' }
  }
}
