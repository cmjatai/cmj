import { defineStore } from 'pinia'
import { markRaw } from 'vue'

// Pilha única de overlays (docs/specs/v8/overlays.md).
//
// Cada entrada descreve um drawer ou modal aberto. O que não pode ser reativo (a função que
// resolve a Promise, o componente, o modo de fechar) fica em `privados`, fora do estado.

const privados = new Map()
let sequencia = 0

const TEXTO_DESCARTAR = {
  titulo: 'Descartar alterações?',
  mensagem: 'Há alterações que não foram salvas. Se fechar agora, elas serão perdidas.',
  rotuloOk: 'Descartar',
  rotuloCancelar: 'Continuar editando',
  variante: 'perigo'
}

function ehCarregador(componente) {
  // Função sem as marcas de um componente Vue é tratada como () => import(...).
  return typeof componente === 'function' && !componente.render && !componente.setup && !componente.__vccOpts
}

export const useOverlayStore = defineStore('overlayStore', {
  state: () => ({
    // Todas as entradas, na ordem de abertura.
    entradas: []
  }),
  getters: {
    // Só as modais: são elas que formam a pilha (V8-OVL-010).
    pilha: state => state.entradas.filter(e => e.modal),
    topo() {
      return this.pilha[this.pilha.length - 1] || null
    },
    // As que o OverlayHost renderiza. As demais são renderizadas por quem as declarou.
    hospedadas: state => state.entradas.filter(e => e.hospedada),
    temAlteracoes: state => state.entradas.some(e => e.dirty)
  },
  actions: {
    entrada(id) {
      return this.entradas.find(e => e.id === id) || null
    },
    conteudo(id) {
      return privados.get(id)?.conteudo || null
    },
    ehTopo(id) {
      return this.topo?.id === id
    },
    // Posição na pilha, usada para a ordem visual (V8-OVL-003).
    ordem(id) {
      return this.entradas.findIndex(e => e.id === id)
    },
    // Quantos drawers modais do mesmo lado estão acima deste (V8-OVL-034).
    profundidade(id) {
      const alvo = this.entrada(id)
      if (!alvo || alvo.kind !== 'drawer') {
        return 0
      }
      const pilha = this.pilha
      const posicao = pilha.findIndex(e => e.id === id)
      return pilha.slice(posicao + 1).filter(e => e.kind === 'drawer' && e.side === alvo.side).length
    },
    registrar(dados = {}) {
      sequencia += 1
      const id = dados.id || `v8-overlay-${sequencia}`
      const opcoes = dados.opcoes || {}
      const entrada = {
        id,
        kind: dados.kind || 'modal',
        type: dados.type || 'default',
        source: dados.source || 'local',
        hospedada: Boolean(dados.hospedada),
        modal: dados.modal !== false,
        side: opcoes.side || 'right',
        opcoes,
        titulo: opcoes.title || '',
        dirty: false,
        chave: dados.chave || null
      }
      let conteudo = dados.conteudo || null
      if (conteudo?.componente && !ehCarregador(conteudo.componente)) {
        conteudo = { ...conteudo, componente: markRaw(conteudo.componente) }
      }
      privados.set(id, {
        conteudo,
        resolver: dados.resolver || null,
        fechador: dados.fechador || null,
        gatilho: dados.gatilho || null
      })
      this.entradas.push(entrada)
      return entrada
    },
    // Tira a entrada da pilha e resolve a Promise de quem a abriu.
    remover(id, valor) {
      const posicao = this.entradas.findIndex(e => e.id === id)
      if (posicao === -1) {
        return
      }
      const privado = privados.get(id)
      privados.delete(id)
      this.entradas.splice(posicao, 1)
      privado?.resolver?.(valor)
    },
    abrir(dados) {
      return new Promise(resolver => {
        this.registrar({ ...dados, hospedada: true, resolver })
      })
    },
    // openModal(componente, props, opcoes): resolve com o valor de close(valor), ou undefined.
    openModal(componente, props = {}, opcoes = {}) {
      return this.abrir({
        kind: 'modal',
        type: opcoes.type || 'default',
        conteudo: { componente, props },
        opcoes
      })
    },
    // openDrawer(conteudo, opcoes): conteudo é { componente, props }, { frag } ou { el }.
    openDrawer(conteudo, opcoes = {}) {
      // O que não é aparência fica fora do estado reativo.
      const { source, chave, fechador, gatilho, ...visuais } = opcoes
      return this.abrir({
        kind: 'drawer',
        conteudo,
        opcoes: visuais,
        modal: (visuais.mode || 'overlay') === 'overlay',
        source: source || 'local',
        chave: chave || null,
        fechador: fechador || null,
        gatilho: gatilho || null
      })
    },
    // confirm(opcoes): resolve true ao confirmar e false ao cancelar ou dispensar (V8-OVL-060).
    confirm(opcoes = {}) {
      return this.abrir({
        kind: 'modal',
        type: 'confirm',
        conteudo: { confirm: true },
        opcoes: { size: 'sm', ...opcoes, title: opcoes.titulo || opcoes.title || 'Confirmar' }
      }).then(valor => valor === true)
    },
    setDirty(id, valor) {
      const entrada = this.entrada(id)
      if (entrada) {
        entrada.dirty = Boolean(valor)
      }
    },
    setTitle(id, titulo) {
      const entrada = this.entrada(id)
      if (entrada) {
        entrada.titulo = titulo || ''
      }
    },
    setModal(id, modal) {
      const entrada = this.entrada(id)
      if (entrada) {
        entrada.modal = Boolean(modal)
      }
    },
    // A entrada e as modais abertas depois dela, da mais nova para a mais velha (V8-OVL-012).
    comAsDeCima(id) {
      const posicao = this.entradas.findIndex(e => e.id === id)
      if (posicao === -1) {
        return []
      }
      return this.entradas
        .slice(posicao)
        .filter((e, i) => i === 0 || e.modal)
        .reverse()
    },
    // Pergunta se as alterações das entradas podem ser descartadas (V8-OVL-024).
    async podeDescartar(ids) {
      const alteradas = ids.map(id => this.entrada(id)).filter(e => e && e.dirty)
      if (!alteradas.length) {
        return true
      }
      const descartar = await this.confirm(TEXTO_DESCARTAR)
      if (descartar) {
        alteradas.forEach(e => {
          e.dirty = false
        })
      }
      return descartar
    },
    // Fechamento pedido pelo usuário: ESC, clique fora, botão de fechar. Respeita a guarda.
    async requestClose(id, valor) {
      const afetadas = this.comAsDeCima(id)
      if (!afetadas.length) {
        return false
      }
      if (!(await this.podeDescartar(afetadas.map(e => e.id)))) {
        return false
      }
      this.close(id, valor)
      return true
    },
    // Fecha sem perguntar. Antes fecha o que foi aberto por cima.
    close(id, valor) {
      this.comAsDeCima(id).forEach(entrada => {
        const fechador = privados.get(entrada.id)?.fechador
        const resultado = entrada.id === id ? valor : undefined
        if (fechador) {
          // Quem guarda o estado (a URL ou a rota) remove a entrada quando ele mudar.
          entrada.dirty = false
          fechador(resultado)
        } else {
          this.remover(entrada.id, resultado)
        }
      })
    },
    // Só para testes: zera a pilha sem resolver nada.
    $limpar() {
      privados.clear()
      this.entradas = []
    }
  }
})
