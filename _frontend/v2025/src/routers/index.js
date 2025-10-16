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
        path: 'painel/:painel_id',
        name: 'painelset_painel_view',
        component: () => import('~@/modules/painelset/Painel.vue'),
        meta: {
          title: '404 - Not Found',
          description: 'Page not found'
        },
        children: [
          {
            path: 'visao/:painelvisao_id?',
            name: 'painelset_painel_visao_view',
            component: () => import('~@/modules/painelset/PainelVisao.vue'),
            meta: {
              title: 'Visão',
              description: 'Visão do painel'
            }
          }
        ]
      },
      {
        path: 'painel/:pathMatch(.*)',
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
