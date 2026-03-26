import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  {
    path: '/',
    name: 'home',
    meta: {
      title: 'Home',
      description: 'Home page'
    },
    children: [
      {
        path: 'v6',
        name: 'app_vue_v6',
        component: () => import('~@/modules/root/RootPage.vue'),
        children: [
          {
            path:'loa',
            name: 'loa_module_view',
            component: () => import('~@/modules/loa/LoaModule.vue'),
            meta: {
              title: 'LOA Module',
              description: 'Home of LOA Module'
            },
            children: [
              {
                'path': 'dashboard',
                name: 'loa_dashboard_link',
                component: () => import('~@/modules/loa/dashboard/LoaDashboard.vue')
              }
            ]
          },
          {
            path: 'sessao',
            name: 'sessao_module_view',
            component: () => import('~@/modules/sessao/SessaoPlenariaModule.vue'),
            meta: {
              title: 'Sessão Module',
              description: 'Home of Sessão Module'
            },
            children: [
              {
                path: '',
                name: 'sessao_plenaria_list_link',
                component: () => import('~@/modules/sessao/SessaoPlenariaList.vue')
              },
              {
                path: ':id',
                name: 'sessao_plenaria_view_link',
                component: () => import('~@/modules/sessao/SessaoPlenariaView.vue')
              }
            ]
          },
          {
            path: 'chat',
            name: 'chat_module_view',
            component: () => import('~@/modules/chat/ChatModule.vue'),
            meta: {
              title: 'Bee IA Chat Module',
              description: 'Home of Bee IA Chat Module'
            },
            children: [
              {
                path: ':sessionId?',
                name: 'chat_session_view',
                component: () => import('~@/modules/chat/ChatSessionView.vue')
              }
            ]
          },
          {
            path: 'arq',
            name: 'arq_layout',
            component: () => import('~@/modules/arq/ArqLayout.vue'),
            meta: {
              title: 'ArqView Module',
              description: 'Módulo de Arquivos'
            },
            children: [
              {
                path: 'admin/:node',
                name: 'arqadminroute',
                component: () => import('~@/modules/arq/admin/AdminLayout.vue'),
                children: [
                  {
                    path: ':nodechild',
                    name: 'arqchildroute',
                    component: () => import('~@/modules/arq/admin/DocListLayout.vue')
                  }
                ]
              },
              {
                path: 'draft',
                name: 'arq_draft',
                component: () => import('~@/modules/arq/draft/DraftManage.vue')
              }
            ]
          },
          {
            path: 'painelsetadmin', // list
            name: 'painelsetadmin_module_admin_view',
            component: () => import('~@/modules/painelset/painelsetadmin/PainelSetModuleAdmin.vue'),
            children: [
              {
                path: '',
                name: 'painelsetadmin_evento_list_link',
                component: () => import('~@/modules/painelset/painelsetadmin/PainelSetEventoList.vue')
              },
              {
                path: ':id/admin',
                name: 'painelsetadmin_admin_link',
                component: () => import('~@/modules/painelset/painelsetadmin/PainelSetAdmin.vue')
              }
            ]
          },
        ]
      },
      {
        path: 'painelset',
        name: 'painelset_module_view',
        component: () => import('~@/modules/painelset/PainelSetModule.vue'),
        meta: {
          title: 'Painelset Module',
          description: 'Home of Painelset Module'
        },
        children: [
          {
            path: 'painel/:painelId?',
            name: 'painelset_painel_view',
            component: () => import('~@/modules/painelset/painel/Painel.vue'),
            meta: {
              title: 'Painel View',
              description: 'View of the painel'
            }
          },
          {
            path: ':pathMatch(.*)',
            name: 'painelset_error_404',
            component: () => import('~@/views/Error404.vue'),
            meta: {
              title: '404 - Not Found',
              description: 'Page not found'
            }
          },
        ]
      },
      {
        path: ':pathMatch(.*)',
        name: 'error_404',
        component: () => import('~@/views/Error404.vue'),
        meta: {
          title: '404 - Not Found',
          description: 'Page not found'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
