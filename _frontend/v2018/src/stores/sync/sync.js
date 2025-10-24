import WebSocketManager from '@/sync/ws/WebSocketManager'
import TimerWorkerService from '@/sync/timer/SyncWorkerService'
import Resources from '@/resources'

import Vue from 'vue'

const syncStore = {
  namespaced: true,
  state: {
    wsManager: null,
    wsConnected: false,
    lastServerSync: null,
    models: {},
    data_cache: {}
  },
  mutations: {
    SET_WS_MANAGER (state, manager) {
      state.wsManager = manager
    },
    SET_WS_CONNECTED (state, status) {
      state.wsConnected = status
    },
    SET_LAST_SERVER_SYNC (state, timestamp) {
      state.lastServerSync = timestamp
    },
    UPDATE_MODEL (state, app_models) {
      if (!state.models[app_models.app]) {
        Vue.set(state.models, app_models.app, {})
      }
      app_models.models.forEach((model) => {
        Vue.set(state.models[app_models.app], model, true)
      })
    },
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
    },
    UPDATE_DATA_CACHE_CRONOMETRO (state, { key, value }) {
      if (!state.data_cache[key]) {
        Vue.set(state.data_cache, key, {})
      }
      Vue.set(state.data_cache[key], value.id, value)
    }
  },
  actions: {

    initWebSocket ({ commit, dispatch, state }) {
      if (state.wsManager) {
        return
      }

      const wsManager = new WebSocketManager()

      wsManager.on('connected', () => {
        commit('SET_WS_CONNECTED', true)
      })
      wsManager.on('disconnected', () => {
        commit('SET_WS_CONNECTED', false)
      })
      wsManager.on('message', (data) => {
        if (data.type === 'sync_refresh.message') {
          dispatch('handleSyncMessage', data.message)
        } else if (data.type === 'pong') {
          // atualizar lastServerSync com o timestamp do servidor
          commit('SET_LAST_SERVER_SYNC', data)
        }
      })
      commit('SET_WS_MANAGER', wsManager)
    },

    sendSyncMessage ({ state }, message) {
      if (state.wsManager && state.wsConnected) {
        state.wsManager.send(message)
      } else {
        console.warn('WebSocket não conectado. Mensagem não enviada:', message)
      }
    },

    handleSyncMessage ({ commit, dispatch, state }, data) {
      const { app, model, id, action, instance, timestamp } = data
      // so processar se o modelo estiver registrado
      if (!state.models[app] || !state.models[app][model]) {
        return
      }

      const uri = `${app}_${model}`
      const inst = { ...(instance || {}), timestamp_frontend: timestamp }
      if (action === 'post_delete') {
        inst.id = inst.id || id
        commit('DELETE_DATA_CACHE', { key: uri, value: inst })
      } else {
        if (!inst.id) {
          // Se instance não tem id, testa se esse id está no cache
          if (id && state.data_cache[uri] && state.data_cache[uri][id]) {
            // timestamp_frontend do cache é menor que o do servidor?
            if (state.data_cache[uri][id].timestamp_frontend < timestamp) {
              dispatch('fetchSync', { app, model, id })
            }
          } else {
            dispatch('fetchSync', { app, model, id })
          }
        } else {
          commit('UPDATE_DATA_CACHE', { key: uri, value: inst })
        }

        // Iniciar cronometro local se for painelset_cronometro e state for 'running'
        if (uri === 'painelset_cronometro' && (inst.state === 'running' || inst.state === 'paused')) {
          dispatch('startLocalCronometro', inst.id)
        }
      }
    },

    async fetchSync ({ commit, dispatch }, { app, model, id, action, params, only_first_page = false }) {
      const _fetch = Resources.Utils.fetch
      const metadata = { app, model }
      if (id) { metadata.id = id }
      if (action) { metadata.action = action }
      if (params) { metadata.query_string = new URLSearchParams(params).toString() }
      return _fetch(
        metadata
      ).then((response) => {
        const uri = `${app}_${model}`
        _.each(response.data.results ? response.data.results : [response.data], (value, idx) => {
          const inst = { ...value, timestamp_frontend: 0 }
          commit('UPDATE_DATA_CACHE', { key: uri, value: inst })

          if (id && uri === 'painelset_cronometro' && (inst.state === 'running' || inst.state === 'paused')) {
            dispatch('startLocalCronometro', inst.id)
          }
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
    },

    // Register models to listen for sync messages
    registerModels ({ commit }, app_models) {
      commit('UPDATE_MODEL', app_models)
    },

    // Timer actions
    startTimer ({ state }, { timerId, callback, interval }) {
      TimerWorkerService.startTimer(timerId, callback, interval)
    },
    stopTimer ({ state }, timerId) {
      TimerWorkerService.stopTimer(timerId)
    },
    startLocalCronometro ({ state, commit }, cronometroId) {
      TimerWorkerService.startTimer(cronometroId, (timestamp) => {
        // console.debug('TIMER', cronometroId, timestamp)
        const cronometro = state.data_cache.painelset_cronometro[cronometroId]
        const lastServerSync = state.lastServerSync
        const server_time_diff = lastServerSync ? lastServerSync.server_time_diff : 0
        // Atualizar cronometro localmente
        if (cronometro && cronometro.state === 'running') {
          // console.debug('TIMER RUNNING', cronometroId, timestamp / 1000, cronometro.started_time, server_time_diff)
          const elapsed_time = ((timestamp - server_time_diff) / 1000) - cronometro.started_time + cronometro.accumulated_time
          cronometro.elapsed_time = elapsed_time
          cronometro.remaining_time = cronometro.duration - elapsed_time
          commit('UPDATE_DATA_CACHE_CRONOMETRO', { key: 'painelset_cronometro', value: cronometro })
        } else if (cronometro && cronometro.state === 'paused') {
          const last_paused_time = ((timestamp - server_time_diff) / 1000) - cronometro.paused_time
          cronometro.last_paused_time = last_paused_time
          commit('UPDATE_DATA_CACHE_CRONOMETRO', { key: 'painelset_cronometro', value: cronometro })
        } else {
          // Parar timer se cronometro não estiver mais 'running' ou 'paused'
          TimerWorkerService.stopTimer(cronometroId)
        }
      }, 500)
    },
    stopLocalCronometro ({ state }, cronometroId) {
      TimerWorkerService.stopTimer(cronometroId)
    }
  }
}

export default syncStore
