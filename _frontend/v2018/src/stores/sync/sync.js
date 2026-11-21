import Resources from '@/resources'

import Vue from 'vue'

const syncStore = {
  namespaced: true,
  state: {
    data_cache: {}
  },
  mutations: {
    DELETE_DATA_CACHE (state, { key, value }) {
      if (state.data_cache[key] && state.data_cache[key][value.id]) {
        // const copy = { ...state.data_cache[key] }
        // delete copy[value.id]
        // Vue.set(state.data_cache, key, copy)
        //
        // state.data_cache[key] = state.data_cache[key]
        Vue.delete(state.data_cache[key], value.id)
      }
    },
    UPDATE_DATA_CACHE (state, { key, value }) {
      if (value.timestamp_frontend) {
        const oldValue = state.data_cache[key] ? state.data_cache[key][value.id] : null
        if (oldValue && oldValue.timestamp_frontend && value.timestamp_frontend) {
          if (value.timestamp_frontend <= oldValue.timestamp_frontend) {
            return
          }
        }
      }
      if (!state.data_cache[key]) {
        Vue.set(state.data_cache, key, {})
      }
      Vue.set(state.data_cache[key], value.id, value)
    }
  },
  actions: {

    async fetchSync ({ commit, dispatch }, {
      app,
      model,
      id,
      action,
      params,
      query_string,
      only_first_page = false,
      method = 'GET'
    }) {
      const _fetch = Resources.Utils.fetch
      const metadata = { app, model, params: params || {} }
      if (id) { metadata.id = id }
      if (action) { metadata.action = action }
      if (query_string) {
        for (const [key, value] of new URLSearchParams(query_string)) {
          metadata.params[key] = value
        }
      }
      params = metadata.params
      metadata.query_string = new URLSearchParams(params).toString()
      return _fetch(
        metadata, method
      ).then((response) => {
        const uri = `${app}_${model}`
        _.each(response.data.results ? response.data.results : [response.data], (value, idx) => {
          const inst = { ...value, timestamp_frontend: 0 }
          commit('UPDATE_DATA_CACHE', { key: uri, value: inst })
        })
        if (!only_first_page && response.data.pagination && response.data.pagination.next_page) {
          dispatch('fetchSync', { app, model, id, action, params: { ...params, page: response.data.pagination.next_page } })
        }
      })
    },

    // Ações de sincronização

    // Sincroniza um item específico
    syncItem ({ dispatch }, { app, model, id }) {
      dispatch('fetchSync', { app, model, id })
    },

    // Invalidações de cache

    // força a remoção do cache de um item de um modelo específico
    invalidateCacheItem ({ commit, state }, { app, model, id }) {
      const uri = `${app}_${model}`
      if (state.data_cache[uri] && state.data_cache[uri][id]) {
        const inst = state.data_cache[uri][id]
        commit('DELETE_DATA_CACHE', { key: uri, value: inst })
      }
    },

    // força a remoção do cache de um modelo específico
    invalidateCacheModels ({ commit, state }, { app, models }) {
      models.forEach(model => {
        const uri = `${app}_${model}`
        if (state.data_cache[uri]) {
          Vue.set(state.data_cache, uri, {})
        }
      })
    },

    // força a remoção do cache de todos os modelos
    invalidateCacheAll ({ commit, state }) {
      Vue.set(state, 'data_cache', {})
    }
  }
}

export default syncStore
