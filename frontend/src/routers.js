
export const routes = [
  {
    path: '/online',
    component: () => import('@/layouts/OnlineLayout'),
    children: [
      { path: '',
        name: 'index_link',
        component: () => import('@/pages/Index.vue')
      },
      {
        path: 'sessao/',
        name: 'sessao_link',
        component: () => import('@/pages/sessao/SessaoPlenariaModule.vue'),
        children: [
          {
            path: 'list/',
            name: 'sessao_list_link',
            component: () => import('@/pages/sessao/SessaoList.vue')
          },
          {
            path: ':id/',
            name: 'sessao_plenaria_online_link',
            component: () => import('@/pages/sessao/SessaoPlenariaOnline.vue')
          }
        ]
      }
    ]
  }
]
