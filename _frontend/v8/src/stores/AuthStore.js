import { defineStore } from 'pinia'
import Resources from '~@/utils/resources'
import { useGlobalStore } from '~@/stores/GlobalStore'

// Estado de quem não tem sessão.
function conexaoAnonima() {
  return {
    is_authenticated: false,
    user: null,
    permissions: []
  }
}

// Monta data_connect com os dados globais que o Django escreveu na página (V8-ARQ-032).
function conexaoDoGlobal(global) {
  if (!global.autenticado || !global.usuario) {
    return conexaoAnonima()
  }
  const usuario = global.usuario
  const user = {
    id: usuario.id,
    username: usuario.username,
    fullname: usuario.nome,
    avatar: usuario.avatar
  }
  if (usuario.votante) {
    user.votante = usuario.votante
  }
  return {
    is_authenticated: true,
    user,
    permissions: [...(global.permissoes || [])]
  }
}

export const useAuthStore = defineStore('authStore', {
  // O store já nasce com o que o GlobalStore tem, sem requisição.
  state: () => ({
    data_connect: conexaoDoGlobal(useGlobalStore())
  }),
  getters: {
    isAuthenticated: (state) => {
      return state.data_connect.is_authenticated || false
    },
    isVotante: (state) => {
      const user = state.data_connect?.user
      return user ? Object.hasOwn(user, 'votante') : false
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
    // Preenche o estado com os dados globais da página, lendo-os se ainda não foram lidos.
    hidratar() {
      const global = useGlobalStore()
      global.carregar()
      this.data_connect = conexaoDoGlobal(global)
      return this.data_connect
    },
    // Aplica a resposta de /api/version. Usada também ao retomar a sessão expirada (V8-HTTP-023).
    aplicarVersao(dados) {
      this.data_connect = dados?.is_authenticated
        ? {
          is_authenticated: true,
          user: dados.user || null,
          permissions: dados.permissions || []
        }
        : conexaoAnonima()
      return this.data_connect
    },
    loginStatus() {
      const utils = Resources.Utils
      const getVersion = utils.getVersion
      return getVersion()
        .then(response => {
          this.aplicarVersao(response.data)
          return response.data
        })
    },
    logoutPortalCMJ() {
      const utils = Resources.Utils
      const logout = utils.logout
      const getVersion = utils.getVersion
      return logout()
        .then(() => {
          return getVersion()
            .then(resp_version => {
              this.aplicarVersao(resp_version.data)
              return resp_version.data
            })
        })
    }
  }
})
