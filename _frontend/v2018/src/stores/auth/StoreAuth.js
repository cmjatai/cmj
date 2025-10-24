import {
  STATE_DATA_CONNECT
} from './mutation-types'

import Resources from '@/resources'

const mutations = {
  [STATE_DATA_CONNECT] (state, data) {
    state.data_connect = data
  }
}

const state = {
  data_connect: {}
}

const getters = {
  user: (state) => {
    return state.data_connect.hasOwnProperty('user') ? state.data_connect.user : null
  },
  isAuthenticated: (state) => {
    return state.data_connect.is_authenticated
  },
  isVotante: (state) => {
    return state.data_connect.hasOwnProperty('votante')
  },
  hasPermission: (state) => {
    return async (perm) => {
      if (!state.data_connect?.initialized) {
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
      return state.data_connect?.permissions?.includes(perm)
    }
  }
}

const actions = {
  loginStatus: ({ commit }) => {
    const utils = Resources.Utils
    const getVersion = utils.getVersion

    let fetch = function () {
      return getVersion()
        .then(response => {
          response.data.initialized = true
          commit(STATE_DATA_CONNECT, response.data)
          return response.data
        })
    }
    return fetch()
  },
  loginPortalCMJ: ({ commit }, { username, password }) => {
    const utils = Resources.Utils
    const login = utils.login
    const getVersion = utils.getVersion

    let fetch = function () {
      return login(username, password)
        .then(response => {
          return getVersion()
            .then(resp_version => {
              response.data.initialized = true
              commit(STATE_DATA_CONNECT, resp_version.data)
              return resp_version.data
            })
        })
    }
    return fetch()
  },
  logoutPortalCMJ: ({ commit }) => {
    const utils = Resources.Utils
    const logout = utils.logout
    const getVersion = utils.getVersion

    let fetch = function () {
      return logout()
        .then(response => {
          return getVersion()
            .then(resp_version => {
              response.data.initialized = true
              commit(STATE_DATA_CONNECT, resp_version.data)
              return resp_version.data
            })
        })
    }
    return fetch()
  }
}
export default {
  state,
  mutations,
  getters,
  actions
}
