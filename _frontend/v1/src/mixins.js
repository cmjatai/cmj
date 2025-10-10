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
      'nivel_detalhe',
      'user'
    ])
  },
  data () {
    return {
      utils: Resources.Utils,
      NIVEL1: 1,
      NIVEL2: 2,
      NIVEL3: 3,
      NIVEL4: 4,
      nulls: [0, '', null, undefined]
    }
  },
  methods: {
    ...Vuex.mapActions([
      'sendMessage',
      'refreshState',
      'getObject',
      'loginPortalCMJ',
      'logoutPortalCMJ',
      'loginStatus',
      'hasPermission'
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
    ws_endpoint (ws) {
      return (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + (ws !== undefined ? ws : this.ws)
    },
    ws_reconnect () {
      this.$disconnect()
      this.$connect()
    },
    on_ws_message (data) {
      let _this = this

      if (_this.app === undefined) {
        return
      }

      if (this.id !== undefined && this.id !== null && data.id !== this.id) {
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
    handleWebSocketMessageTimeRefresh (event) {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      let data = JSON.parse(event.data)
      // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
      // console.log(performance.now(), 'ws-message', data)
      this
        .$nextTick(() => {
          // console.log(performance.now(), 'ws-message-exec', data)
          EventBus.$emit('ws-message', data.message)
          // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
        })
    },
    handleWebSocketMessageTimeRefresh_deprecated (event) {
      /**
       * Define um ouvinte para o socket implementado por VueNativeSock
       */
      let data = JSON.parse(event.data)
      // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
      // console.log(performance.now(), 'ws-message', data)
      this.$nextTick(() => {
        this.refreshState(data.message)
          .then(value => {
            // Emite um evento pelo barramento parelelo global.
            // O componente que estiver ouvindo esse barramento será informado que um
            // evento ws-message ocorreu. Será chamada o method on_ws_message
            console.log(performance.now(), 'ws-message-exec', data)
            EventBus.$emit('ws-message', data.message)
            // this.sendMessage({ alert: 'info', message: 'Base Atualizada', time: 3 })
          })
          .catch(err => {
            console.error('Erro ao atualizar o estado da aplicação', err)
          })
      })
    },
    fetchModelOrderedList (app = null, model = null, ordering = null, page = 1, query_string = '', func = null) {
      if (page === null || model === null || ordering === null) {
        return
      }
      const t = this
      return t.utils.getModelOrderedList(app, model, ordering, page, query_string)
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
                t.fetchModelOrderedList(app, model, ordering, response.data.pagination.next_page, query_string)
              } else {
                _.mapKeys(t.itens[`${model}_list`], function (obj, k) {
                  if (!t.nulls.includes(obj) && !obj.vue_validate) {
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
    },
    user_logged_in () {
    },
    user_logged_out () {
    }
  },
  created: function () {
    /*
      Observador para o WebSocket...
      O Componente que se interesse por monitorar notificacões vindas
      do servidor de que um model possui alteracão, basta re-implementar
      o método on_ws_message, ou usar o on_ws_message do mixin e implementar o fetch
    */
    let _this = this
    EventBus.$on('ws-message', _this.on_ws_message)
    EventBus.$on('user-logged-in', _this.user_logged_in)
    EventBus.$on('user-logged-out', _this.user_logged_out)
  }
})
