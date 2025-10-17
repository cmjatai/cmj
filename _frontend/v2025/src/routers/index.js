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
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
