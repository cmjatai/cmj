
import './__globals'
import Vue from 'vue'
import Vuex from 'vuex'
import VueResize from 'vue-resize'
import BootstrapVue from 'bootstrap-vue'
import VueNativeSock from 'vue-native-websocket'
import Router from 'vue-router'

import VuexStore from './store'

import axios from 'axios'

import { sync } from 'vuex-router-sync'
import { loadProgressBar } from 'axios-progress-bar'

import 'axios-progress-bar/dist/nprogress.css'
import 'vue-resize/dist/vue-resize.css'

import 'popper.js'

import { routes } from './routers'

import App from './App'

import './mixins'

axios.defaults.headers.get['Cache-Control'] = 'no-cache, no-store, must-revalidate'
axios.defaults.headers.get['Pragma'] = 'no-cache' // Suporte para navegadores mais antigos
axios.defaults.headers.get['Expires'] = '0' // Expira imediatamente
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(Vuex)
Vue.use(Router)
Vue.use(VueResize)
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
  // reconnection: true // (Boolean) whether to reconnect automatically (false)
  connectManually: true,
  format: 'json' // (String) send and receive data in JSON format (json)
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
  el: '#app',
  components: { App },
  template: '<App/>'
})

Storage.prototype.addArrayOfIds = function (key, id) {
  let ids = this.getItem(key) || '[]'
  ids = JSON.parse(ids)
  let idx = ids.indexOf(id)
  if (idx === -1) {
    ids.push(id)
    return this.setItem(key, JSON.stringify(ids))
  }
}
Storage.prototype.getArrayOfIds = function (key) {
  return JSON.parse(this.getItem(key))
}
Storage.prototype.inArrayOfIds = function (key, id) {
  let ids = this.getItem(key) || '[]'
  ids = JSON.parse(ids)
  return ids.indexOf(id) !== -1
}
Storage.prototype.delItemArrayOfIds = function (key, id) {
  let ids = this.getItem(key) || '[]'
  ids = JSON.parse(ids)
  ids.splice(ids.indexOf(id), 1)
  this.setItem(key, JSON.stringify(ids))
}
Storage.prototype.clearArrayOfIds = function (key) {
  this.removeItem(key)
}
