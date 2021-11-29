import { defineNuxtConfig } from 'nuxt3'

import path from 'path'

// https://v3.nuxtjs.org/docs/directory-structure/nuxt.config
export default defineNuxtConfig({
  buildModules: [
    '@vueuse/core/nuxt'
  ],
  css: [
    '@/assets/scss/main.scss'
  ],
})
