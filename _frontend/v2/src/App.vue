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
      /*
      let r = (this.offsetHeight - window.scrollY * 1.7) / (this.offsetHeight)

      let h = document.getElementsByTagName('header')[0]
      let p = document.getElementsByClassName('btns-main')[0]

      let portallogo = document.getElementById('portallogo')
      let portalsearch = document.getElementById('portalsearch')
      // let rowlogo = document.getElementById('rowlogo')

      let left = portallogo.offsetWidth
      let right = portalsearch.offsetWidth

      console.log(window.scrollY, r)

      h.style.height = `${this.offsetHeight * r}px`

      if (window.scrollY > 60) {
        h.style.marginTop = `${(60 - window.scrollY)}px`
        p.style.left = `${left}px`
        p.style.right = `${right}px`
        p.style.top = 0
        // rowlogo.classList.add('align-items-center')
        // rowlogo.classList.remove('align-items-top')
      } else {
        h.style.marginTop = '0px'
        p.style.top = 'auto'
        p.style.left = `${left * (1.2 - r)}px`
        p.style.right = `${left * (1.2 - r)}px`
        // rowlogo.classList.remove('align-items-center')
        // rowlogo.classList.add('align-items-top')
      }

      if (window.scrollY > 60) {
      } else {
      }

      /*

      if (r > 0) { p.style.opacity = r }

        // h.style.marginTop = '0px'
        if (window.scrollY < 60) {
          p.style.opacity = 1
          p.style.left = `${left * (1 - r)}px`
          p.style.right = `${right * (1 - r)}px`
        } else if (window.scrollY < 150) {
          p.style.left = `${left}px`
          p.style.right = `${right}px`
        }
      }

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
      */
    },
    teste: function (env) {
      console.log('teste')
    }
  },
  mounted: function () {
    window.addEventListener('scroll', this.handleScroll)

    /* let h = document.getElementsByTagName('header')[0]
    this.offsetHeight = h.offsetHeight

    this.ro = new ResizeObserver(entries => {
      let m = document.getElementsByTagName('main')[0]
      m.style.marginTop = `${entries[0].target.offsetHeight}px`
    })

    this.ro.observe(h) */

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
