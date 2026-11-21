import { defineStore } from 'pinia'

// Dados globais que o Django escreve em <script id="v8-global"> (V8-ARQ-023 e V8-ARQ-032).
export const ID_DADOS_GLOBAIS = 'v8-global'

export function dadosPadrao() {
  return {
    versao: '',
    debug: false,
    autenticado: false,
    usuario: null,
    permissoes: [],
    urls: {
      api: '/api',
      versao: '/api/version',
      sessao: '/api/auth/session',
      login: '/login/',
      logout: '/logout/',
      base: '/v8/',
      frag: '/v8/_frag/'
    },
    zonas: {},
    zona: null,
    flags: {},
    tema: null,
    sidebar: 'expandida'
  }
}

export function lerJson(id) {
  const el = document.getElementById(id)
  if (!el) {
    return null
  }
  try {
    return JSON.parse(el.textContent)
  } catch {
    return null
  }
}

export const useGlobalStore = defineStore('globalStore', {
  state: () => ({
    ...dadosPadrao(),
    carregado: false
  }),
  getters: {
    prefixoZona: state => (state.zona ? state.zonas[state.zona] || null : null)
  },
  actions: {
    carregar() {
      if (this.carregado) {
        return
      }
      const lido = lerJson(ID_DADOS_GLOBAIS)
      const padrao = dadosPadrao()
      if (lido && typeof lido === 'object' && !Array.isArray(lido)) {
        Object.keys(padrao).forEach(chave => {
          if (lido[chave] !== undefined) {
            this[chave] = chave === 'urls' ? { ...padrao.urls, ...lido.urls } : lido[chave]
          }
        })
      }
      this.carregado = true
    }
  }
})
