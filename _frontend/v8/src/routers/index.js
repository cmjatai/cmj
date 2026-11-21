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
