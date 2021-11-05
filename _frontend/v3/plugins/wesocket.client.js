import { defineNuxtPlugin } from '#app'
import VueNativeSock from 'vue-native-websocket-vue3'


export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(VueNativeSock, 'wss://www.jatai.go.leg.br/ws/time-refresh/')
})