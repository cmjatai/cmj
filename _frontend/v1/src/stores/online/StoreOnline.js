import {
  STATE_UPDATE,
  STATE_DELETE,
  SET_NIVEL_DETALHE
} from './mutation-types'

import Resources from '@/resources'

const mutations = {
  [STATE_DELETE] (state, wsdata) {
    let data = wsdata
    if (!state.cache.hasOwnProperty(data.app)) {
      return
    }
    if (!state.cache[data.app].hasOwnProperty(data.model)) {
      return
    }
    if (!state.cache[data.app][data.model][data.id]) {
      return
    }
    delete state.cache[data.app][data.model][data.id]
  },
  [STATE_UPDATE] (state, data) {
    if (!state.cache.hasOwnProperty(data.app)) {
      state.cache[data.app] = {}
    }
    if (!state.cache[data.app].hasOwnProperty(data.model)) {
      state.cache[data.app][data.model] = {}
    }
    state.cache[data.app][data.model][data.value !== undefined ? data.value.id : data.id] = data.value
  },

  [SET_NIVEL_DETALHE] (state, nivel) {
    state.nivel_detalhe = nivel
  }
}

const state = {
  cache: {},
  nivel_detalhe: 1
}

const getters = {
  cache: (state) => {
    return state.cache
  },
  nivel_detalhe: (state) => {
    return state.nivel_detalhe
  },
  getCache: (state) => (metadata) => {
    if (!state.cache.hasOwnProperty(metadata.app)) {
      return null
    }
    if (!state.cache[metadata.app].hasOwnProperty(metadata.model)) {
      return null
    }
    if (!state.cache[metadata.app][metadata.model].hasOwnProperty(metadata.id)) {
      return null
    }
    return state.cache[metadata.app][metadata.model]
  }
}

const actions = {
  setNivelDetalhe: ({ commit }, nivel) => {
    commit(SET_NIVEL_DETALHE, nivel)
  },
  getObject: ({ commit, getters, dispatch }, metadata) => {
    let model = getters.getCache(metadata)

    if (model !== null && model[metadata.id]) {
      return model[metadata.id]
    }

    return dispatch('refreshState', metadata)
      .then(value => {
        return value
      })
  },
  refreshState: ({ commit }, metadata) => {
    if (metadata.hasOwnProperty('value')) {
      return new Promise((resolve, reject) => {
        commit(STATE_UPDATE, metadata)
        resolve()
      })
    }

    if (metadata.action === 'post_delete') {
      return new Promise((resolve, reject) => {
        commit(STATE_DELETE, metadata)
        resolve()
      })
    }

    const utils = Resources.Utils
    const resource = metadata.func === undefined ? utils.getModel : metadata.func

    let fetch = function () {
      let exec = resource === utils.getModel ? resource(metadata.app, metadata.model, metadata.id) : resource(metadata)

      return exec
        .then(response => {
          let meta = {
            app: metadata.app,
            model: metadata.model,
            value: response.data,
            id: response.data.id
          }
          commit(STATE_UPDATE, meta)
          return response.data
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
