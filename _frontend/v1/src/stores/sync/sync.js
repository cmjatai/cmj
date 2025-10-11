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
    handleSyncMessage ({ commit, dispatch }, data) {
      const { app, model, action, instance, timestamp } = data
      const uri = `${app}_${model}`
      const inst = { ...(instance || {}), timestamp_frontend: timestamp }
      if (action === 'post_delete') {
        commit('DELETE_DATA_CACHE', { key: uri, value: inst })
      } else {
        commit('UPDATE_DATA_CACHE', { key: uri, value: inst })

        // Iniciar cronometro local se for painelset_cronometro e state for 'running'
        if (uri === 'painelset_cronometro' && (inst.state === 'running' || inst.state === 'paused')) {
          dispatch('startLocalCronometro', inst.id)
        }
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
    },
    startLocalCronometro ({ state, commit }, cronometroId) {
      TimerWorkerService.startTimer(cronometroId, (timestamp) => {
        // console.log('TIMER', cronometroId, timestamp)
        const cronometro = state.data_cache.painelset_cronometro[cronometroId]
        const lastServerSync = state.lastServerSync
        const server_time_diff = lastServerSync ? lastServerSync.server_time_diff : 0
        // Atualizar cronometro localmente
        if (cronometro && cronometro.state === 'running') {
          const elapsed_time = (timestamp / 1000) - cronometro.started_time + server_time_diff + cronometro.accumulated_time
          cronometro.elapsed_time = elapsed_time
          cronometro.remaining_time = cronometro.duration - elapsed_time
          commit('UPDATE_DATA_CACHE', { key: 'painelset_cronometro', value: cronometro })
        } else if (cronometro && cronometro.state === 'paused') {
          const last_paused_time = (timestamp / 1000) - cronometro.paused_time + server_time_diff + cronometro.accumulated_time
          cronometro.last_paused_time = last_paused_time
          commit('UPDATE_DATA_CACHE', { key: 'painelset_cronometro', value: cronometro })
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
