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
      scrollAtivo: true

    }
  },
  methods: {
    handleScroll: function (event) {
      let h = document.getElementsByTagName('header')[0]
      console.log(event)
      if (window.scrollY === 0) {
        h.style.marginTop = '0px'
        h.classList.add('header-top')
      } else if (window.scrollY > 0 && window.scrollY <= 200 && h.classList.contains('header-top')) {
        h.style.marginTop = '0px'
        h.classList.remove('header-top')
      } else {
        // h.classList.remove('header-top')
        if (window.scrollY > 200) {
          h.style.marginTop = `${-1 * (window.scrollY - 200)}px`
        } else {
          h.style.marginTop = '0px'
        }
      }
    },
    teste: function (env) {
      console.log('teste')
    }
  },
  mounted: function () {
    window.addEventListener('scroll', this.handleScroll)

    this.ro = new ResizeObserver(entries => {
      // let m = document.getElementsByTagName('main')[0]
      // m.style.marginTop = `${entries[0].target.offsetHeight}px`

      // console.log('resizeHeader')
      // this.scrollAtivo = true
    })

    let h = document.getElementsByTagName('header')[0]
    this.ro.observe(h)

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
