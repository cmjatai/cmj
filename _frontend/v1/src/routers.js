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
        path: ':pkloa(\\d+)',
        name: 'loadetail_route',
        component: () => import('@/modules/loa/LoaDetail')
      },
      {
        path: 'dash',
        name: 'loadash_route',
        component: () => import('@/modules/loa/LoaDash')
      }
    ]
  },
  {
    path: '/online/',
    component: () => import('@/modules/online/OnlineLayout'),
    children: [
      {
        path: 'sessao', // list
        name: '',
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
      },
      { path: 'painelset', // list
        name: 'painelset_list_link',
        component: () => import('@/modules/painelset/PainelSetModule.vue'),
        children: [
          {
            path: ':id/',
            name: 'painelset_detail_link',
            component: () => import('@/modules/painelset/PainelSetDetail.vue'),
            children: [
              {
                path: 'admin',
                name: 'painelset_admin_link',
                component: () => import('@/modules/painelset/admin/PainelSetAdmin.vue')
              },
              {
                path: ':painel_id',
                name: 'painelset_painel_link',
                component: () => import('@/modules/painelset/painel/PainelSetPainel.vue')
              }
            ]
          }
        ]
      }
    ]
  }
]
