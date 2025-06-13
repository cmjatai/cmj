import { createRouter, createWebHistory } from 'vue-router'

const Error404 = () => import('~@/views/Error404.vue')

export const routes = [
  {
    path: '/:pathMatch(.*)',
    name: 'error_404',
    component: Error404,
    meta: {
      title: '404 - Not Found',
      description: 'Page not found',
    },
  },
  {
    path: '/loa/',
    component: () => import('~@/views/loa/LoaLayout'),
    name: 'loa_route',
    children: [
      {
        path: 'dash',
        name: 'loadash_route',
        component: () => import('~@/views/loa/LoaDashboard')
      }
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
