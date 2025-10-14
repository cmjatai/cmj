import 'vite/modulepreload-polyfill'
// Add the necessary CSS

// Import our custom CSS
import '~@/scss/styles.scss'
// import '@fortawesome/fontawesome-free/js/all.js'

// Import all of Bootstrap's JS

import * as bootstrap from 'bootstrap'
// import 'bootstrap-icons/font/bootstrap-icons.scss'

import axios from 'axios'

import './js/utils'

import { onMounted, createApp } from 'vue'
import {createBootstrap} from 'bootstrap-vue-next'

import { createPinia } from 'pinia'
import router from './js/routers'

import EventBus from './js/EventBus'
import rootComponents from './rootComponents'
import { useWsTimeRefresh } from './js/composables/WsTimeRefresh'

document.querySelectorAll('[data-bs-toggle="popover"]')
  .forEach(popover => {
    new bootstrap.Popover(popover)
  })

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const app = createApp({
  components: rootComponents,
  setup() {

    const protocol = (window.location.protocol === 'https:' ? 'wss://' : 'ws://')
    const ws_url = protocol + window.location.host + '/ws/time-refresh/'

    const wsTimeRefresh = useWsTimeRefresh(ws_url)
    wsTimeRefresh.connect()

    onMounted(() => {
      /* Enable this to test the time refresh
      setTimeout(() => {
        wsTimeRefresh.send(
          {message:'Time refresh requested'}
        )
      }, 3000)*/
    })
  },
  delimiters: ['[[', ']]'],
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

