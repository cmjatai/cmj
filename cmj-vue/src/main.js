import Vue from 'vue'
import Vuex from 'vuex';
import Router from 'vue-router';
import VueResource from 'vue-resource';
import { sync } from 'vuex-router-sync';

import App from './App.vue'
import VuexStore from './vuex/store';
import { routes } from './router-config';

Vue.use(Vuex);
Vue.use(Router);
Vue.use(VuexStore);
Vue.use(VueResource);

Vue.http.headers.common['Access-Control-Allow-Origin'] = '*';

const store = new Vuex.Store(VuexStore);

const router = new Router({
  routes,
  mode: 'history',
  saveScrollPosition: true,
});

sync(store, router);

const app = new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app-vue');

let { x, y, ...z } = { x: 1, y: 5, a: 3, b: 4 };
console.log(x); // 1
console.log(y); // 2
console.log(z); // { a: 3, b: 4 }
