<template>
  <message></message>
</template>

<script>
import Message from '../components/utils/message/Message.vue'
import EventBus from './event-bus'

export default {
  components: { Message },
  name: 'Push',
  mounted: function () {
    const t = this
    this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })

    t.$options.sockets.onmessage = (event) => {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      const data = JSON.parse(event.data)

      setTimeout(() => {
        EventBus.$emit('ws-message', data.message)
        // Atualiza em Vuex/cache o elemento que o Servidor informou ter sofrido alteracão
        // t.refreshState(data.message)
        //  .then(value => {
        // Emite um evento pelo barramento parelelo global.
        // O componente que estiver ouvindo esse barramento será informado que um
        // evento ws-message ocorreu. Será chamada o method on_ws_message
        // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
        //  })
      }, 500)
    }
  }
}
</script>

<style lang="scss">

</style>
