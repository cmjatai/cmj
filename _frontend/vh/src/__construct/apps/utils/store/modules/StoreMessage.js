import {
  MESSAGE_SHIFT,
  MESSAGE_POP
} from '../mutation-types'

const mutations = {
  [MESSAGE_SHIFT] (state, data) {
    state.messages.unshift(data)
    setTimeout(function () {
      state.messages.pop()
    }, 5000)
  },
  [MESSAGE_POP] (state) {
    state.messages.pop()
  }
}

const state = {
  messages: []
}

const getters = {
  getMessages: state => state.messages
}

const actions = {
  sendMessage: ({ commit }, data) => commit(MESSAGE_SHIFT, data),
  popMessage: ({ commit }) => commit(MESSAGE_POP)
}
export default {
  state,
  mutations,
  getters,
  actions
}
