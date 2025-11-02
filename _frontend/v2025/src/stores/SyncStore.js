import { defineStore } from 'pinia'
import TimerWorkerService from '~@/utils/timer/TimerWorkerService'
import WebSocketManager from '~@/utils/ws/WebSocketManager'
import Resources from '~@/utils/resources'

export const useSyncStore = defineStore('syncStore', {
  state: () => ({
    // Define your state properties here
    wsManager: null,
    wsConnected: false,
    lastServerSync: null,
    models: {},
    data_cache: {}
  }),
  getters: {
    // Define your getters here
  },
  actions: {
    // Define your actions here
    initialize() {
      if (this.wsManager) {
        return
      }
      this.wsManager = new WebSocketManager()
      this.wsManager.on('open', () => {
        this.wsConnected = true
      })
      this.wsManager.on('close', () => {
        this.wsConnected = false
      })
      this.wsManager.on('message', (data) => {
        if (data.type === 'pong') {
          this.lastServerSync = data
        } else if (data.type === 'sync_refresh.message') {
          this.handleSyncMessage(data.message)
        }
      })
    },
    DELETE_DATA_CACHE ({ key, value }) {
      if (this.data_cache[key] && this.data_cache[key][value.id]) {
        delete this.data_cache[key][value.id]
      }
    },
    UPDATE_DATA_CACHE_CRONOMETRO ({ key, value }) {
      if (!this.data_cache[key]) {
        this.data_cache[key] = {}
      }
      this.data_cache[key][value.id] = value
    },


    UPDATE_DATA_CACHE ({ key, value }) {
      if (value.timestamp_frontend) {
        const oldValue = this.data_cache[key] ? this.data_cache[key][value.id] : null
        if (oldValue && oldValue.timestamp_frontend && value.timestamp_frontend) {
          if (value.timestamp_frontend <= oldValue.timestamp_frontend) {
            return
          }
        }
      }
      if (value.__label__) {
        const objsInValue = Object.keys(value).filter(key => {
          return typeof value[key] === 'object' && value[key] !== null
        })
        objsInValue.forEach(objKey => {
          let nestedKey = value[objKey].__label__
          if (!nestedKey) {
            return
          }
          nestedKey = nestedKey.replace('.', '_')
          this.UPDATE_DATA_CACHE({ key: nestedKey, value: value[objKey] })
        })
      } else {
        value.__label__ = key
      }
      if (!this.data_cache[key]) {
        this.data_cache[key] = {}
      }
      this.data_cache[key][value.id] = value
    },

    async fetchSync ({ app, model, id, action, params, only_first_page = false, force_fetch = true}) {
      const _fetch = Resources.Utils.fetch
      if (!this.models[app] || !this.models[app][model]) {
        //faz auto registro do modelo
        this.registerModels(app, [model])
      }
      if (!force_fetch) {
        const uri = `${app}_${model}`
        if (id && this.data_cache[uri] && this.data_cache[uri][id]) {
          return this.data_cache[uri][id]
        } else if (!id && this.data_cache[uri]) {
          return Object.values(this.data_cache[uri])
        }
      }
      const metadata = { app, model }
      if (id) { metadata.id = id }
      if (action) { metadata.action = action }
      if (params) {
        if (!params.o) {
          params.o = 'id'
        }
        metadata.params = params
        Object.keys(params).forEach((key) => {
          if (Array.isArray(params[key])) {
            metadata.params[key] = params[key].join(',')
          }
        })
      }
      return _fetch(
        metadata
      ).then((response) => {
        const uri = `${app}_${model}`
        _.each(response.data.results ? response.data.results : [response.data], (value) => {
          const inst = { ...value, timestamp_frontend: 0 }
          this.UPDATE_DATA_CACHE({ key: uri, value: inst })
        })
        if (!only_first_page && response.data.pagination && response.data.pagination.next_page) {
          return this.fetchSync({ app, model, id, action, params: { ...params, page: response.data.pagination.next_page } })
        }
        return this.data_cache[uri]
      })
    },

    sendSyncMessage (message) {
      if (this.wsManager && this.wsConnected) {
        this.wsManager.send(message)
      } else {
        console.warn('WebSocket não conectado. Mensagem não enviada:', message)
      }
    },

    handleSyncMessage(message) {
      const { app, model, id, action, instance, timestamp } = message
      if (!this.models[app] || !this.models[app][model]) {
        return
      }

      const key = `${app}_${model}`
      const inst = { ...(instance || {}), timestamp_frontend: timestamp }

      if (action === 'post_delete') {
        delete this.data_cache[key][id]
      }
      else if (action === 'post_save') {
        if (!inst.id) {
          if (id && this.data_cache[key] && this.data_cache[key][id]) {
            if (this.data_cache[key][id].timestamp_frontend < timestamp) {
              this.fetchSync({ app, model, id })
            }
          } else {
            this.fetchSync({ app, model, id })
          }
        } else {
          this.UPDATE_DATA_CACHE({ key, value: inst })
        }

        if (key === 'painelset_cronometro' && (inst.state === 'running' || inst.state === 'paused')) {
          this.startLocalCronometro(inst.id)
        }
      }
    },

    invalidateDataCache(apps = null, models = null) {
      if (apps && models) {
        apps.forEach(app => {
          models.forEach(model => {
            if (this.models[app] && this.models[app][model]) {
              const key = `${app}_${model}`
              this.data_cache[key] = {}
            }
          })
        })
        return
      }
    },
    invalidateCacheItems(app, model, ids) {
      if (!this.models[app] || !this.models[app][model]) {
        return
      }
      const key = `${app}_${model}`
      if (!this.data_cache[key]) {
        return
      }
      ids.forEach(id => {
        if (this.data_cache[key][id]) {
          delete this.data_cache[key][id]
        }
      })
    },

    registerModels(app, models) {
      if (!this.models[app]) {
        this.models[app] = {}
      }
      models.forEach(model => {
        if (!this.models[app][model]) {
          this.models[app][model] = true
        }
      })
    },

    // Timer functions for cronometro
    startLocalCronometro(id) {
      TimerWorkerService.startTimer(id, (timestamp) => {
        // console.debug('TIMER', cronometroId, timestamp)
        const cronometro = this.data_cache.painelset_cronometro[id]
        const lastServerSync = this.lastServerSync
        const server_time_diff = lastServerSync ? lastServerSync.server_time_diff : 0
        // Atualizar cronometro localmente
        if (cronometro && cronometro.state === 'running') {
          // console.debug('TIMER RUNNING', id, timestamp / 1000, cronometro.started_time, server_time_diff)
          const elapsed_time = ((timestamp - server_time_diff) / 1000) - cronometro.started_time + cronometro.accumulated_time
          cronometro.elapsed_time = elapsed_time
          cronometro.remaining_time = cronometro.duration - elapsed_time
          this.UPDATE_DATA_CACHE_CRONOMETRO({ key: 'painelset_cronometro', value: cronometro })
        } else if (cronometro && cronometro.state === 'paused') {
          const last_paused_time = ((timestamp - server_time_diff) / 1000) - cronometro.paused_time
          cronometro.last_paused_time = last_paused_time
          this.UPDATE_DATA_CACHE_CRONOMETRO({ key: 'painelset_cronometro', value: cronometro })
        } else {
          // Parar timer se cronometro não estiver mais 'running' ou 'paused'
          TimerWorkerService.stopTimer(id)
        }
      }, 500)
    },
    stopLocalCronometro(id) {
      TimerWorkerService.stopTimer(id)
    }
  }
})
