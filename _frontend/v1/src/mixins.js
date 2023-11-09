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
      'getObject'
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
      return typeof value === 'string' || value instanceof String
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
        } else {
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
    },

    fetchModelListAction (app = null, model = null, action = null, page = 1, func = null) {
      if (page === null || model === null || action === null) {
        return
      }

      const t = this
      return t.utils.getModelListAction(app, model, action, page)
        .then((response) => {
          t.init = true
          _.each(response.data.results, (value, idx) => {
            value.vue_validate = true
            if (value.id in t.itens[`${model}_list`]) {
              t.itens[`${model}_list`][value.id] = value
            } else {
              t.$set(t.itens[`${model}_list`], value.id, value)
            }
            if (func !== null) {
              func(value)
            }
          })
          t.$nextTick()
            .then(function () {
              if (response.data.pagination.next_page !== null) {
                t.fetchModelListAction(app, model, action, response.data.pagination.next_page)
              } else {
                _.mapKeys(t.itens[`${model}_list`], function (obj, k) {
                  if (!obj.vue_validate) {
                    t.$delete(t.itens[`${model}_list`], obj.id)
                  }
                })
              }
            })
        })
        .catch((response) => {
          t.init = true
          t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a Listagem.', time: 5 })
        })
    },
    removeAside () {
      const main = document.getElementsByTagName('main')
      const aside = document.getElementsByTagName('aside')
      const wrapper = document.getElementById('wrapper')

      const parent = aside[0].parentElement
      parent.removeChild(aside[0])

      wrapper.id = ''

      main[0].classList.add('appvue')
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
