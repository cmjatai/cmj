import Vue from 'vue'
import Vuex from 'vuex'

import { EventBus } from '@/event-bus'

Vue.use(Vuex)

Vue.mixin({

  computed: {
    ...Vuex.mapGetters([
      'getModel'
    ])
  },
  methods: {
    ...Vuex.mapActions([
      'sendMessage',
      'removeFromState',
      'insertInState'
    ]),
    stringToDate: function (_date, _format, _delimiter) {
      var formatLowerCase = _format.toLowerCase()
      var formatItems = formatLowerCase.split(_delimiter)
      var dateItems = _date.split(_delimiter)
      var monthIndex = formatItems.indexOf('mm')
      var dayIndex = formatItems.indexOf('dd')
      var yearIndex = formatItems.indexOf('yyyy')
      var month = parseInt(dateItems[monthIndex])
      month -= 1
      var formatedDate = new Date(dateItems[yearIndex], month, dateItems[dayIndex])
      return formatedDate
    },
    on_ws_message (data) {
      let _this = this

      if (!_this.hasOwnProperty('app') || !_this.hasOwnProperty('model')) {
        return
      }

      if (Array.isArray(_this.app) && Array.isArray(_this.model)) {
        if (_.indexOf(_this.app, data.message.app) !== -1 &&
            _.indexOf(_this.model, data.message.model) !== -1) {
          _this.fetch()
        }
      } else {
        if (data.message.app === _this.app && data.message.model === _this.model) {
          _this.fetch()
        }
      }
    }
  },
  created: function () {
    /*
      Observador para o WebSocket...
      O Componente que se interesse por monitorar notificacões vindas
      do servidor de que um model possui alteracão, basta implementar
      o método on_ws_message.
    */
    let _this = this
    EventBus.$on('ws-message', _this.on_ws_message)
  }
})
