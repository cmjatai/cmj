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
  data () {
    return {
      ro: null,
      offsetHeight: 0
    }
  },
  methods: {
    handleScroll: function (event) {
      let h = document.getElementsByTagName('header')[0]
      let r = (window.scrollY / $(document).height())

      // console.log(r, h.offsetHeight)
      if (window.scrollY === 0) {
        h.style.marginTop = '0px'
        h.classList.add('header-top')
      } else {
        h.classList.remove('header-top')
      }

      if (window.scrollY * 1.5 > this.offsetHeight) {
        h.style.marginTop = `${(-3 * r * h.offsetHeight)}px`
      }
    }
  },
  mounted: function () {
    window.addEventListener('scroll', this.handleScroll)

    let h = document.getElementsByTagName('header')[0]
    this.offsetHeight = h.offsetHeight

    this.ro = new ResizeObserver(entries => {
      let m = document.getElementsByTagName('main')[0]
      m.style.marginTop = `${entries[0].target.offsetHeight - 1}px`
    })

    this.ro.observe(h)

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
