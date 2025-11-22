import 'vite/modulepreload-polyfill'
// Add the necessary CSS

// Import our custom CSS
import '~@/scss/styles.scss'
// import '@fortawesome/fontawesome-free/js/all.js'

// Import all of Bootstrap's JS

import * as bootstrap from 'bootstrap'
import {createBootstrap} from 'bootstrap-vue-next'

// import 'bootstrap-icons/font/bootstrap-icons.scss'

import axios from 'axios'

import './utils'

import { library } from '@fortawesome/fontawesome-svg-core'

/* import all the icons in Free Solid, Free Regular, and Brands styles */
import { fas } from '@fortawesome/free-solid-svg-icons'
import { far } from '@fortawesome/free-regular-svg-icons'
import { fab } from '@fortawesome/free-brands-svg-icons'

library.add(fas, far, fab)

import { createApp } from 'vue'

import { createPinia } from 'pinia'
import router from './routers'

import EventBus from './utils/EventBus'
import registerComponents from './registerComponents'

document.querySelectorAll('[data-bs-toggle="popover"]')
  .forEach(popover => {
    new bootstrap.Popover(popover)
  })

axios.defaults.headers.get['Cache-Control'] = 'no-cache, no-store, must-revalidate'
axios.defaults.headers.get['Pragma'] = 'no-cache' // Suporte para navegadores mais antigos
axios.defaults.headers.get['Expires'] = '0' // Expira imediatamente

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const app = createApp({
  delimiters: ['[[', ']]'],
  components: registerComponents.rootComponents,
  setup() {
  }
})

Object.keys(registerComponents.globalComponents).forEach(name => {
  app.component(name, registerComponents.globalComponents[name])
})

// EventBus para comunicação entre componentes via Composite API
app.provide('EventBus', EventBus)
// EventBus para comunicação entre componentes via Option API
app.config.globalProperties.$EventBus = EventBus

app
  .use(router)
  .use(createPinia())
  .use(createBootstrap())
  .mount('#cmj')

// Registro manual do Service Worker para controle total da URL
if ('serviceWorker' in navigator) {
  // Define a URL baseada no modo (Dev ou Prod) conforme configurado no vite.config.js
  const swUrl = '/v2025/service-worker.js'

  console.debug('Environment Mode:', import.meta.env.MODE)

  navigator.serviceWorker.register(swUrl, { scope: '/v2025/' , type: 'module' })
    .then((registration) => {
      console.debug('Service Worker registrado com sucesso no escopo:', registration.scope)
    })
    .catch((error) => {
      console.error('Falha ao registrar o Service Worker:', error)
    })
}

