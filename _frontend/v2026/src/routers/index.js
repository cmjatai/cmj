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
        path: 'v2026',
        name: 'app_vue_v2026',
        component: () => import('~@/modules/root/RootPage.vue'),
        children: [
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
          }
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
          }
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
