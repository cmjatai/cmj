import './registerServiceWorker'
import { createApp } from 'vue'
import BodyBaseDjangoTemplate from './root/BodyBaseDjangoTemplate'
import VueNativeSock from 'vue-native-websocket-vue3'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import { loadFonts } from './plugins/webfontloader'
import mixins from './mixins'
loadFonts()

let portal = createApp({
  delimiters: ['[[', ']]'],
  extends: {
    ...BodyBaseDjangoTemplate
  }
}).use(store).use(router).use(vuetify)

portal = portal.use(VueNativeSock, (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/time-refresh/', {
  connectManually: true
})

portal.mixin(mixins)

portal.mount('#app-vue')
