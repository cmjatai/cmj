// Registro de painéis (V8-OVL-050): o nome usado em data-drawer="<nome>:<argumento>" e em
// ?painel=<nome>:<argumento>. `props` transforma o argumento da URL nas props do componente.
export const paineis = {
  cliente: {
    componente: () => import('~@/modules/demo/paineis/PainelCliente.vue'),
    props: arg => ({ id: Number(arg) }),
    opcoes: { side: 'right', size: 'md', title: 'Cliente' }
  }
}
