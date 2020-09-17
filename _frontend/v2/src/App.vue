<template>
    <message></message>
</template>

<script>
import Message from '@/components/utils/message/Message'
import { EventBus } from '@/event-bus'
export default {
  name: 'app',
  components: {
    Message
  },
  methods: {
    handleScroll: function (event) {
      let h = document.getElementsByTagName('header')[0]
      if (window.scrollY === 0) {
        h.classList.add('header-top')
      } else {
        h.classList.remove('header-top')
      }
    },
    teste: function (env) {
      console.log('teste')
    }
  },
  mounted: function () {
    window.addEventListener('scroll', this.handleScroll)

    // let h = document.getElementsByTagName('header')[0]
    // h.style.height = `${self.innerHeight * 1}px`

    this.$options.sockets.onmessage = (event) => {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      let data = JSON.parse(event.data)
      // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })

      setTimeout(() => {
        // Atualiza em Vuex/cache o elemento que o Servidor informou ter sofrido alteracão
        this.refreshState(data.message)
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
