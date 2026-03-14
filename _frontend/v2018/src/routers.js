// { path: '',
//   name: 'index_link',
//   component: () => import('@/pages/Index.vue')
// },

export const routes = [
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
