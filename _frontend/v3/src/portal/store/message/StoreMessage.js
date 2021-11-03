import {
  MESSAGE_SHIFT,
  MESSAGE_POP
} from './mutation-types'

const mutations = {
  [MESSAGE_SHIFT] (state, data) {
    data.id = state.messageId++

    if (data.time === undefined) {
      data.time = 3
    }

    state.messages.unshift(data)
  },
  [MESSAGE_POP] (state, messageId) {
    _.remove(state.messages, function (msg) {
      return messageId === msg.id
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
  popMessage: ({ commit }, messageId) => commit(MESSAGE_POP, messageId)
}
export default {
  state,
  mutations,
  getters,
  actions
}
