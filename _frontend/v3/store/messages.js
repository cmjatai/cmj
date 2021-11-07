const MESSAGE_SHIFT = 'MESSAGE_SHIFT'
const MESSAGE_POP = 'MESSAGE_POP'

export const state = () => ({
  messages: [],
  counterId: 0
})

export const getters = {
  getMessages: (state) => {
    return state.messages
  }
}

export const actions = {
  sendMessage: ({ commit }, data) => commit(MESSAGE_SHIFT, data),
  popMessage: ({ commit }, messageId) => commit(MESSAGE_POP, messageId),

}

export const mutations = {
  [MESSAGE_SHIFT] (state, data) {
    data.id = state.counterId++

    if (data.time === undefined) {
      data.time = 3
    }

    state.messages.unshift(data)
  },
  [MESSAGE_POP] (state, message) {
    const i = state.messages.indexOf(message)
    state.messages.splice(i,1)
  }
}
