// Zona SPA da demonstração (V8-DEMO-020 e 021). Os caminhos são relativos ao prefixo da zona,
// que vem do Django (/v8/demo/spa): o router os acrescenta como filhos da rota da zona.
//
// O detalhe do cliente e o pedido são rotas aninhadas com `meta.drawer`: quem as desenha é o
// <DrawerRota> do componente da rota pai, dentro de um drawer (V8-OVL-053).
import DemoSpaLayout from '~@/modules/demo/spa/DemoSpaLayout.vue'

export default {
  layout: DemoSpaLayout,
  rotas: [
    {
      path: '',
      name: 'demo_spa_inicio',
      redirect: { name: 'demo_spa_clientes' }
    },
    {
      path: 'clientes',
      name: 'demo_spa_clientes',
      component: () => import('~@/modules/demo/spa/ClientesLista.vue'),
      meta: { breadcrumb: 'Clientes' },
      children: [
        {
          path: ':id(\\d+)',
          name: 'demo_spa_cliente',
          component: () => import('~@/modules/demo/spa/ClienteDetalhe.vue'),
          props: route => ({ id: Number(route.params.id) }),
          meta: {
            breadcrumb: 'Cliente',
            drawer: { side: 'right', size: 'md', title: 'Cliente' }
          },
          children: [
            {
              path: 'pedidos/:pedido(\\d+)',
              name: 'demo_spa_pedido',
              component: () => import('~@/modules/demo/spa/PedidoDetalhe.vue'),
              props: route => ({
                id: Number(route.params.id),
                pedido: Number(route.params.pedido)
              }),
              meta: {
                breadcrumb: 'Pedido',
                drawer: { side: 'right', size: 'sm', title: 'Pedido' }
              }
            }
          ]
        }
      ]
    }
  ]
}
