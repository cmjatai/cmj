<template>
  <div id="app-frontend-base-content">
    <message></message>
    <router-view></router-view>
  </div>
</template>

<script>
import Message from '@/components/utils/message/Message'
import { EventBus } from '@/event-bus'
export default {
  name: 'app',
  components: {
    Message
  },
  mounted: function () {
    this.$options.sockets.onmessage = (event) => {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      let data = JSON.parse(event.data)
      this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })

      // Remove do Vuex/cache o elemento que o Servidor informou ter sofrido alteracão
      this.removeFromState(data)

      // Emite um evento pelo barramento parelelo global.
      // O componente que estiver ouvindo esse barramento será informado que um
      // evento ws-message ocorreu. Será chamada o method on_ws_message
      EventBus.$emit('ws-message', data)
    }
  }
}
</script>

<style lang="scss">

</style>
