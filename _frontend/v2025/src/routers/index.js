import { createRouter, createWebHistory } from 'vue-router'

const WsTest = () => import('~@/views/WsTest.vue')
const Error404 = () => import('~@/views/Error404.vue')

export const routes = [
  {
    path: '/v2025/',
    name: 'home',
    meta: {
      title: 'Home',
      description: 'Home page',
    },
    children: [
      {
        path: '/wstest/',
        name: 'index_link',
        component: WsTest,
        children: [
        ]
      },
      {
        path: '/:pathMatch(.*)',
        name: 'error_404',
        component: Error404,
        meta: {
          title: '404 - Not Found',
          description: 'Page not found',
        },
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
