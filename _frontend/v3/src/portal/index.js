import { createApp } from 'vue'
import BodyBaseDjangoTemplate from './root/BodyBaseDjangoTemplate'
import VueNativeSock from 'vue-native-websocket-vue3'
import router from './router'
import store from './store'

import mixins from './mixins'

let portal = createApp({
  delimiters: ['[[', ']]'],
  extends: {
    ...BodyBaseDjangoTemplate
  }
}).use(store).use(router)

portal = portal.use(VueNativeSock, (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/time-refresh/', {
  connectManually: true
})

portal.mixin(mixins)

portal.mount('#app-vue')

export default portal
