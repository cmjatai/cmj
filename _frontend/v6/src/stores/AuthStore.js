import { defineStore } from 'pinia'
import Resources from '~@/utils/resources'

export const useAuthStore = defineStore('authStore', {
  state: () => ({
    data_connect: {}
  }),
  getters: {
    isAuthenticated: (state) => {
      return state.data_connect.is_authenticated || false
    },
    isVotante: (state) => {
      return state.data_connect?.user?.hasOwnProperty('votante') || false
    },
    permissions: (state) => {
      return state.data_connect?.permissions || []
    },
    hasPermission: (state) => {
      return (perm) => {

        if (!state.data_connect.permissions) {
          return false
        }
        return state.data_connect.permissions.includes(perm)
      }
    }
  },
  actions: {
    loginStatus() {
      const utils = Resources.Utils
      const getVersion = utils.getVersion
      return getVersion()
        .then(response => {
          this.data_connect = response.data
          return response.data
        })
    },
    loginPortalCMJ(username, password) {
      const utils = Resources.Utils
      const login = utils.login
      const getVersion = utils.getVersion
      return login(username, password)
        .then(response => {
          return getVersion()
            .then(resp_version => {
              this.data_connect = resp_version.data
              return resp_version.data
            })
        })
    },
    logoutPortalCMJ() {
      const utils = Resources.Utils
      const logout = utils.logout
      const getVersion = utils.getVersion
      return logout()
        .then(response => {
          return getVersion()
            .then(resp_version => {
              this.data_connect = resp_version.data
              return resp_version.data
            })
        })
    }
  }
})
