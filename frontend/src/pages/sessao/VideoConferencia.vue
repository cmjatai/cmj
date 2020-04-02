<template>
  <div class="w-100 h-100 d-flex inner-video-conferencia">
    <div class="inner-meet" id="meet"></div>
  </div>
</template>

<script>
export default {
  name: 'video-conferencia',
  data () {
    return {
      api: null
    }
  },
  computed: {
    visivel: function () {
      return this.is_nivel(this.NIVEL4)
    }
  },
  watch: {
    visivel: function (nv, old) {
      if (nv) {
        this.api = undefined
        const domain = 'jitsih.interlegis.leg.br'
        const options = {
          roomName: 'CMJTeste',
          width: '100%',
          height: '100%',
          parentNode: document.querySelector('#meet'),
          interfaceConfigOverwrite: { TOOLBAR_BUTTONS: ['hangup', 'microphone', 'camera'] }
        }
        this.api = new window.JitsiMeetExternalAPI(domain, options)
        this.api.executeCommand('displayName', `User ${Math.random()}`)
        this.api.executeCommand('toggleTileView')
        this.api.executeCommand('subject', 'CMJTeste')
        // api.executeCommand('password', '12345');
        // api.executeCommand('toggleChat');

        this.api.on('readyToClose', () => {
          console.log('Closed session')
          // window.location.href = "{% url 'sapl.sdr:deliberacaoremota_list' %}"
        })
      } else {
        this.api.dispose()
      }
    }
  },
  methods: {
  },
  mounted () {
  }
}
</script>

<style lang="scss">

@import "~@/scss/variables";

.inner-video-conferencia {
  // background: linear-gradient(to right, rgba(9, 20, 38, 0.95) 0%, #000000 100%);
  position: relative;
  .inner-meet {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
  }
}
</style>
