import Vue from 'vue'
import Vuex from 'vuex'

import Resources from '@/resources'
import { EventBus } from '@/event-bus'

Vue.use(Vuex)

Vue.mixin({

  computed: {
    ...Vuex.mapGetters([
      'getCache',
      'cache',
      'nivel_detalhe'
    ])
  },
  data () {
    return {
      utils: Resources.Utils,
      NIVEL1: 1,
      NIVEL2: 2,
      NIVEL3: 3,
      NIVEL4: 4
    }
  },
  methods: {
    ...Vuex.mapActions([
      'sendMessage',
      'refreshState',
      'getObject',
    ]),
    nivel (value, teste_local) {
      return this.nivel_detalhe >= value && teste_local ? '' : 'd-none'
    },
    month_text (month_num) {
      let month = [
        'Janeiro',
        'Fevereiro',
        'Março',
        'Abril',
        'Maio',
        'Junho',
        'Julho',
        'Agosto',
        'Setembro',
        'Outubro',
        'Novembro',
        'Dezembro'
      ]
      return month[month_num]
    },
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
    isString: function (value) {
      return typeof value === 'string' || value instanceof String;
    },
    on_ws_message (data) {
      let _this = this

      if (_this.app === undefined) {
        return
      }
      
      if (_this.model === undefined) {
        if (Array.isArray(_this.app)) {
          if (_.indexOf(_this.app, data.app) !== -1) {
            _this.fetch(data)
          }
        }
        else {
          if (data.app === _this.app) {
            _this.fetch(data)
          }
        }
      } else if (Array.isArray(_this.app) && Array.isArray(_this.model)) {
        if (_.indexOf(_this.app, data.app) !== -1 &&
            _.indexOf(_this.model, data.model) !== -1) {
          _this.fetch(data)
        }
      } else {
        if (data.app === _this.app && data.model === _this.model) {
          _this.fetch(data)
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
