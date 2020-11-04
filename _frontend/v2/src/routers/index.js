// { path: '',
//   name: 'index_link',
//   component: () => import('@/pages/Index.vue')
// },

export const routes = [
  {
    path: '',
    component: () => import('@/views/Root.vue'),
    children: [
      {
        path: '/online',
        component: () => import('@/__apps/online/layouts/OnlineLayout'),
        children: [
          {
            path: '', // list
            name: 'sessao_link',
            component: () => import('@/__apps/online/pages/sessao/SessaoPlenariaModule.vue'),
            children: [
              {
                path: '',
                name: 'sessao_list_link',
                component: () => import('@/__apps/online/pages/sessao/SessaoList.vue')
              },
              {
                path: ':id/',
                name: 'sessao_plenaria_online_link',
                component: () => import('@/__apps/online/pages/sessao/SessaoPlenariaOnline.vue')
              }
            ]
          }
        ]
      },
      {
        name: 'documento_construct',
        path: '/documento/:id/construct',
        component: () => import('@/__apps/sigad/components/DocumentoEdit.vue')
      },
      {
        name: 'documento_construct_create',
        path: '/classe/:id/documento/construct',
        component: () => import('@/__apps/sigad/components/DocumentoEdit.vue')
      }

    ]
  }

  // {
  //   path: '*',
  //   name: '404',
  //   component: {
  //     template: '<p>Page Not Found</p>'
  //   }
  // }
]
