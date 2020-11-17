<template>
    <message></message>
</template>

<script>
import { EventBus } from '@/event-bus'
export default {
  name: 'app',
  components: {
    Message: () => import('@/components/utils/message/Message')
  },
  data () {
    return {
    }
  },
  methods: {
    handleScroll: function (event) {
      let h = document.getElementsByTagName('header')[0]
      let u = document.getElementById('user_connected')
      if (u && window.location.pathname !== '/') {
        h.classList.remove('header-top')
        h.classList.add('header-mini')
        return
      }
      if (window.scrollY === 0) {
        h.classList.remove('header-mini')
        if (!u && window.location.pathname === '/') {
          h.classList.add('header-top')
        }
        // console.log('topo', window.scrollY)
      } else if (window.scrollY > 220 && window.scrollY < 300) {
        if (h.classList.contains('header-mini') || h.classList.contains('header-top')) {
          h.classList.remove('header-top')
          h.classList.remove('header-mini')
        }
        // console.log('meio', window.scrollY)
      } else if (window.scrollY > 400) {
        if (!h.classList.contains('header-mini')) {
          h.classList.add('header-mini')
          h.classList.remove('header-top')
          // console.log('fim', window.scrollY)
        }
      } else {
        // console.log('limbo', window.scrollY)
      }
    }
  },
  mounted: function () {
    let h = document.getElementsByTagName('header')[0]
    let u = document.getElementById('user_connected')

    if (u && window.location.pathname !== '/') {
      h.classList.remove('header-top')
      h.classList.add('header-mini')
      return
    }

    window.addEventListener('scroll', this.handleScroll)

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
