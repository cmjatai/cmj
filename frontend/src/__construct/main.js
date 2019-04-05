import Vue from 'vue'
import Vuex from 'vuex'
import VueResource from 'vue-resource'
import VueResize from 'vue-resize'
import BootstrapVue from 'bootstrap-vue'
// import VueCookie from 'vue-cookie'
// import lodash from 'lodash'

import Router from 'vue-router'
import { sync } from 'vuex-router-sync'

import VuexStore from './apps/store'
import { routes } from './router-config'

import axios from 'axios'
import { loadProgressBar } from 'axios-progress-bar'
import 'axios-progress-bar/dist/nprogress.css'

//import VueFroala from 'vue-froala-wysiwyg'
import 'vue-resize/dist/vue-resize.css'

import Components from './apps'

//require('froala-editor/js/froala_editor.pkgd.min')
//require('froala-editor/css/froala_editor.pkgd.min.css')
require('font-awesome/css/font-awesome.css')
//require('froala-editor/css/froala_style.min.css')

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(Vuex)
Vue.use(Router)
Vue.use(VueResource)
//Vue.use(VueFroala)
Vue.use(VueResize)
Vue.use(BootstrapVue)
Vue.config.productionTip = false

// Vue.http.headers.common['Access-Control-Allow-Origin'] = '*'

loadProgressBar()

const store = new Vuex.Store(VuexStore)
const router = new Router({
  routes,
  mode: 'history',
  saveScrollPosition: true
})

sync(store, router)

const app = new Vue({ // eslint-disable-line
  router,
  store,
  components: Components.components,
  el: '#app-vue'
})
