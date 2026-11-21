import { defineStore } from 'pinia'

// Fila de toasts (docs/specs/v8/overlays.md, seção Toasts).
//
// O estado guarda só o que a tela mostra. A contagem de cada toast (tempo restante, início e o
// timer) fica em `contagens`, fora do estado reativo.

export const MAXIMO_VISIVEIS = 4
export const NIVEIS = ['success', 'info', 'warning', 'error']

// Tempo de vida por nível, em ms. `null`: só sai ao ser dispensado (V8-OVL-071).
export const DURACOES = {
  success: 4000,
  info: 5000,
  warning: 7000,
  error: null
}

const contagens = new Map()
let sequencia = 0

function duracaoDe(nivel, duracao) {
  if (duracao === undefined) {
    return DURACOES[nivel]
  }
  return Number.isFinite(duracao) && duracao > 0 ? duracao : null
}

export const useToastStore = defineStore('toastStore', {
  state: () => ({
    // Os que estão na tela, do mais antigo para o mais novo.
    visiveis: [],
    // Os que aguardam vaga, na ordem de chegada.
    fila: []
  }),
  actions: {
    adicionar({ nivel, texto, duracao } = {}) {
      const toast = {
        id: ++sequencia,
        nivel: NIVEIS.includes(nivel) ? nivel : 'info',
        texto: String(texto ?? '')
      }
      contagens.set(toast.id, {
        restante: duracaoDe(toast.nivel, duracao),
        inicio: 0,
        timer: null,
        pausado: false
      })
      if (this.visiveis.length < MAXIMO_VISIVEIS) {
        this.visiveis.push(toast)
        this._contar(toast.id)
      } else {
        this.fila.push(toast)
      }
      return toast.id
    },
    dispensar(id) {
      const contagem = contagens.get(id)
      if (contagem?.timer) {
        clearTimeout(contagem.timer)
      }
      contagens.delete(id)

      const naFila = this.fila.findIndex(t => t.id === id)
      if (naFila !== -1) {
        this.fila.splice(naFila, 1)
        return true
      }
      const naTela = this.visiveis.findIndex(t => t.id === id)
      if (naTela === -1) {
        return false
      }
      this.visiveis.splice(naTela, 1)
      // A contagem do próximo só começa quando ele entra na tela.
      while (this.visiveis.length < MAXIMO_VISIVEIS && this.fila.length) {
        const proximo = this.fila.shift()
        this.visiveis.push(proximo)
        this._contar(proximo.id)
      }
      return true
    },
    // Para a contagem e guarda o tempo que faltava.
    pausar(id) {
      const contagem = contagens.get(id)
      // Só o que está na tela tem contagem para pausar.
      if (!contagem || contagem.pausado || !this.visiveis.some(t => t.id === id)) {
        return
      }
      contagem.pausado = true
      if (contagem.timer) {
        clearTimeout(contagem.timer)
        contagem.timer = null
        contagem.restante = Math.max(0, contagem.restante - (Date.now() - contagem.inicio))
      }
    },
    retomar(id) {
      const contagem = contagens.get(id)
      if (!contagem || !contagem.pausado) {
        return
      }
      contagem.pausado = false
      if (this.visiveis.some(t => t.id === id)) {
        this._contar(id)
      }
    },
    // Dispensa todos, visíveis e em fila.
    limpar() {
      contagens.forEach(contagem => clearTimeout(contagem.timer))
      contagens.clear()
      this.visiveis = []
      this.fila = []
    },
    _contar(id) {
      const contagem = contagens.get(id)
      if (!contagem || contagem.pausado || contagem.timer || contagem.restante === null) {
        return
      }
      contagem.inicio = Date.now()
      contagem.timer = setTimeout(() => this.dispensar(id), contagem.restante)
    }
  }
})
