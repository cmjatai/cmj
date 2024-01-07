// { path: '',
//   name: 'index_link',
//   component: () => import('@/pages/Index.vue')
// },

export const routes = [
  {
    path: '/arq/',
    component: () => import('@/modules/arq/ArqLayout'),
    children: [
      {
        path: 'draft',
        component: () => import('@/modules/arq/draft/DraftManage')
      },
      {
        path: ':node/',
        name: 'arqadminroute',
        component: () => import('@/modules/arq/admin/AdminLayout'),
        children: [
          {
            path: ':nodechild/',
            name: 'arqchildroute',
            component: () => import('@/modules/arq/admin/DocListLayout')
          }
        ]
      }
    ]
  },
  {
    path: '/online',
    component: () => import('@/modules/online/OnlineLayout'),
    children: [
      {
        path: '', // list
        name: 'sessao_link',
        component: () => import('@/modules/online/sessao/SessaoPlenariaModule.vue'),
        children: [
          {
            path: '',
            name: 'sessao_list_link',
            component: () => import('@/modules/online/sessao/SessaoList.vue')
          },
          {
            path: ':id/',
            name: 'sessao_plenaria_online_link',
            component: () => import('@/modules/online/sessao/SessaoPlenariaOnline.vue')
          }
        ]
      }
    ]
  }
]
