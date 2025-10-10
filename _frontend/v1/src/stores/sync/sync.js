import WebSocketManager from '@/sync/ws/WebSocketManager'
import TimerWorkerService from '@/sync/timer/TimerWorkerService'
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
      if (state.lastServerSync === null || timestamp > state.lastServerSync) {
        state.lastServerSync = timestamp
      }
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
        Vue.delete(state.data_cache[key], value.id)
      }
    },
    UPDATE_DATA_CACHE (state, { key, value }) {
      const oldValue = state.data_cache[key] ? state.data_cache[key][value.id] : null
      if (oldValue && oldValue.timestamp_frontend && value.timestamp_frontend) {
        if (value.timestamp_frontend <= oldValue.timestamp_frontend) {
          return
        }
      }
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
        if (data.type === 'sync') {
          dispatch('handleSyncMessage', data)
        } else if (data.type === 'pong') {
          // atualizar lastServerSync com o timestamp do servidor
          commit('SET_LAST_SERVER_SYNC', data.timestamp)
        }
      })
      commit('SET_WS_MANAGER', wsManager)
    },
    handleSyncMessage ({ commit, state }, data) {
      const { app, model, action, instance, timestamp } = data
      const uri = `${app}_${model}`
      const inst = { ...(instance || {}), timestamp_frontend: timestamp }
      if (action === 'post_delete') {
        commit('DELETE_DATA_CACHE', { key: uri, value: inst })
      } else {
        commit('SET_LAST_SERVER_SYNC', timestamp)
        commit('UPDATE_DATA_CACHE', { key: uri, value: inst })
      }
    },
    registerModels ({ commit }, app_models) {
      commit('UPDATE_MODEL', app_models)
    },
    startTimer ({ state }, { timerId, callback, interval }) {
      TimerWorkerService.startTimer(timerId, callback, interval)
    },
    stopTimer ({ state }, timerId) {
      TimerWorkerService.stopTimer(timerId)
    }
  }
}

export default syncStore
