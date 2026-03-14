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
    path: '/loa/',
    component: () => import('@/modules/loa/LoaLayout'),
    name: '',
    children: [
      {
        path: '',
        name: 'loalist_route',
        component: () => import('@/modules/loa/LoaList')
      },
      {
        path: ':pkloa(\\d+)/despesa',
        name: 'loadetail_route',
        component: () => import('@/modules/loa/LoaDetail')
      },
      {
        path: ':pkloa(\\d+)/prestacaocontaloa',
        name: 'prestacaocontaloa_route',
        component: () => import('@/modules/loa/pcl/PrestacaoContaLoaLayout')
      },
      {
        path: 'dash',
        name: 'loadash_route',
        component: () => import('@/modules/loa/LoaDash')
      }
    ]
  }
]
