import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const About = () => import('../views/About.vue')
const About2 = () => import('../views/About2.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/about',
    name: 'About',
    component: About
  },
  {
    path: '/about2',
    name: 'About2',
    component: About2
  }

]

const router = createRouter({
  saveScrollPosition: true,
  history: createWebHistory('/'),
  routes
})

export default router
