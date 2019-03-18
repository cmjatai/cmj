/*
- App SaplFrontend - que será transformada em PWA.
- Já possui comunicacão com o backend via websocket e contará
com refresh online da tela do usuário.
- atualmente invocada sobre o Sapl de layout tradicional via link /online
*/

import './__globals'
import Vue from 'vue'
import Vuex from 'vuex'
import BootstrapVue from 'bootstrap-vue'
import VueNativeSock from 'vue-native-websocket'
import Router from 'vue-router'

import VuexStore from './store'

import axios from 'axios'

import { sync } from 'vuex-router-sync'
import { loadProgressBar } from 'axios-progress-bar'
import 'axios-progress-bar/dist/nprogress.css'

import { routes } from './routers'

import App from './App'

import './mixins'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(Vuex)
Vue.use(Router)
Vue.use(BootstrapVue)

/*
ws/time-refresh recebe uma notificacão sempre que um model do Sapl
é alterado. Um JSON é enviado pelo servidor no formato:
{
  action: 'post_save' | 'post_delete',
  id: 9999, // 9999 - pk do model alterado
  app: 'app_name', // de que app é esse id
  model; 'model_name', // de que model é esse id
}
*/

Vue.use(VueNativeSock, (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/time-refresh/', {
  reconnection: true // (Boolean) whether to reconnect automatically (false)
  // reconnectionAttempts: 5, // (Number) number of reconnection attempts before giving up (Infinity),
  // reconnectionDelay: 3000, // (Number) how long to initially wait before attempting a new (1000)
})

loadProgressBar()

Vue.config.productionTip = false

const store = new Vuex.Store(VuexStore)
const router = new Router({
  routes,
  mode: 'history'
})
sync(store, router)

const app = new Vue({ // eslint-disable-line
  router,
  store,
  el: '#app-frontend-base-content',
  components: { App },
  template: '<App/>'
})
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').then(registration => {
      // console.log('SW registered: ', registration);
    }).catch(registrationError => {
      console.log('SW registration failed: ', registrationError);
    });
  });
}