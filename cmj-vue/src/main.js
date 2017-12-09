import Vue from 'vue'
import Vuex from 'vuex'
import VueCookie from 'vue-cookie'
import VueResource from 'vue-resource'

import Router from 'vue-router'
  import { sync } from 'vuex-router-sync'

import VueFroala from 'vue-froala-wysiwyg'
  require('froala-editor/js/froala_editor.pkgd.min')
  require('froala-editor/css/froala_editor.pkgd.min.css')
  require('font-awesome/css/font-awesome.css')
  require('froala-editor/css/froala_style.min.css')

import lodash from 'lodash'

import Components from './apps'
import VuexStore from './apps/store'
import { routes } from './router-config'

import axios from 'axios'
  import { loadProgressBar } from 'axios-progress-bar'
  axios.defaults.xsrfCookieName = 'csrftoken'
  axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(Vuex)
Vue.use(Router)
Vue.use(VueResource)
Vue.use(VueFroala)

//Vue.http.headers.common['Access-Control-Allow-Origin'] = '*'

loadProgressBar()

const store = new Vuex.Store(VuexStore)
const router = new Router({
  routes,
  mode: 'history',
  saveScrollPosition: true,
})

sync(store, router)

const app = new Vue({
  router,
  store,
  components: Components.components,
  el: '#app-vue'
})


//let { x, y, ...z } = { x: 1, y: 2, a: 3, b: 4 }
//console.log(x)
//console.log(y)
//console.log(z)

// editor: npm install vue-froala-wysiwyg --save
// drag and grop: npm install --save vddl    https://github.com/hejianxian/vddl
