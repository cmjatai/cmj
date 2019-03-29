import {
  STATE_UPDATE,
  STATE_DELETE
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
    return 
  },
  [STATE_UPDATE] (state, data) {
     if (!state.cache.hasOwnProperty(data.app)) {
      state.cache[data.app] = {}
    }
    if (!state.cache[data.app].hasOwnProperty(data.model)) {
      state.cache[data.app][data.model] = {}
    }
    state.cache[data.app][data.model][
      data.value !== undefined ? data.value.id : data.id] = data.value 
  }
}

const state = {
  cache: {}
}

const getters = {
  cache: (state) => {
    return state.cache
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
  getObject: ({ commit, getters, dispatch }, metadata) => {
    let model = getters.getCache(metadata)

    if (model !== null && model[metadata.id])
      return model[metadata.id]
    
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

    let fetch = function () {
      let utils = Resources.Utils
      //console.log('fetch refresh', metadata)
      return utils
        .getModel(metadata.app, metadata.model, metadata.id)
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
  },
}
export default {
  state,
  mutations,
  getters,
  actions
}
