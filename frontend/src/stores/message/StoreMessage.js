import {
  MESSAGE_SHIFT,
  MESSAGE_POP
} from './mutation-types'

const mutations = {
  [MESSAGE_SHIFT] (state, data) {
    data.id = state.counter_id++
    state.messages.unshift(data)
  },
  [MESSAGE_POP] (state, message_id) {
    _.remove(state.messages, function (msg) {
      return message_id === msg.id
    })
  }
}

const state = {
  messages: [],
  counter_id: 0
}

const getters = {
  getMessages: state => state.messages
}

const actions = {
  sendMessage: ({ commit }, data) => commit(MESSAGE_SHIFT, data),
  popMessage: ({ commit }, message_id) => commit(MESSAGE_POP, message_id)
}
export default {
  state,
  mutations,
  getters,
  actions
}
