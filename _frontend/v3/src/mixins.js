import EventBus from './root/event-bus'
import Vuex from 'vuex'

export default {
  computed: {
  },
  data () {
    return {
    }
  },
  methods: {
    ...Vuex.mapActions([
      'sendMessage'
    ]),
    on_ws_message (data) {
    }
  },
  created: function () {
    console.log('created mixin')
    /*
      Observador para o WebSocket...
      O Componente que se interesse por monitorar notificacões vindas
      do servidor de que um model possui alteracão, basta implementar
      o método on_ws_message.
    */
    const t = this
    EventBus.$on('ws-message', t.on_ws_message)
  }
}