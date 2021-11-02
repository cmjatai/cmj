<template>
  <div class="container-messages">
    teste compomente
  </div>
</template>

<script>
import { EventBus } from './event-bus'

export default {
  name: 'Push',
  mounted_old: function () {
    const t = this

    t.$options.sockets.onmessage = (event) => {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      const data = JSON.parse(event.data)
      // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })

      setTimeout(() => {
        // Atualiza em Vuex/cache o elemento que o Servidor informou ter sofrido alteracão
        t.refreshState(data.message)
          .then(value => {
            // Emite um evento pelo barramento parelelo global.
            // O componente que estiver ouvindo esse barramento será informado que um
            // evento ws-message ocorreu. Será chamada o method on_ws_message
            EventBus.$emit('ws-message', data.message)
            // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
          })
      }, 500)
    }
  }
}
</script>

<style lang="scss">

</style>
