<template>
  <DialogRoot
    v-if="modal"
    :open="true"
    @update:open="aoMudarAberto"
  >
    <DialogPortal>
      <Transition
        name="v8-t-scrim"
        appear
      >
        <DialogOverlay
          v-if="aberto"
          force-mount
          :class="['v8-scrim', camada, { 'v8-scrim-transparente': !comScrim }]"
          :style="estiloOrdem"
        />
      </Transition>
      <Transition
        :name="transicao"
        appear
        @after-leave="emit('saiu')"
      >
        <DialogContent
          v-if="aberto"
          force-mount
          :class="classesModal"
          :style="estilo"
          :role="papel"
          aria-modal="true"
          :aria-describedby="undefined"
          :data-overlay-id="id"
          :data-overlay-kind="kind"
          :data-overlay-topo="ehTopo ? '' : undefined"
          @pointer-down-outside="aoInteragirFora"
          @interact-outside="aoInteragirFora"
        >
          <header class="v8-overlay-cabecalho">
            <DialogTitle class="v8-overlay-titulo">
              {{ titulo }}
            </DialogTitle>
            <button
              type="button"
              class="v8-btn v8-btn-fantasma v8-btn-icone"
              aria-label="Fechar"
              data-overlay-fechar
              @click="pedirFechamento"
            >
              <svg
                class="v8-icone"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                aria-hidden="true"
              >
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </header>
          <div class="v8-overlay-corpo">
            <Encaixe :el="conteudoEl" />
          </div>
          <footer class="v8-overlay-rodape">
            <Encaixe :el="rodapeEl" />
          </footer>
        </DialogContent>
      </Transition>
    </DialogPortal>
  </DialogRoot>

  <Teleport
    v-else
    :to="doca"
    :disabled="!doca || modo !== 'docked'"
  >
    <aside
      v-if="aberto"
      :class="classesLateral"
      :style="estilo"
      role="complementary"
      :aria-labelledby="idTitulo"
      :data-overlay-id="id"
      :data-overlay-kind="kind"
    >
      <header class="v8-overlay-cabecalho">
        <h2
          :id="idTitulo"
          class="v8-overlay-titulo"
        >
          {{ titulo }}
        </h2>
        <button
          type="button"
          class="v8-btn v8-btn-fantasma v8-btn-icone"
          aria-label="Fechar"
          data-overlay-fechar
          @click="pedirFechamento"
        >
          <svg
            class="v8-icone"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </header>
      <div class="v8-overlay-corpo">
        <Encaixe :el="conteudoEl" />
      </div>
      <footer class="v8-overlay-rodape">
        <Encaixe :el="rodapeEl" />
      </footer>
    </aside>
  </Teleport>

  <!-- O conteúdo vem depois da moldura: um overlay declarado dentro dele monta por cima. -->
  <Teleport :to="conteudoEl">
    <slot />
  </Teleport>
</template>
<script setup>
// Moldura única de drawers e modals (overlays.md). É usada pelo OverlayHost, para o que é aberto
// pelo store, e direto em templates, para o que é declarado por rota ou por componente.
//
// Em modo modal a moldura é um Dialog do Reka UI, que cuida de foco, fundo inerte, rolagem e
// ARIA. Em `push` e `docked` é um <aside> comum (V8-OVL-032).

// 1. Imports
import { computed, onBeforeUnmount, provide, ref, watch, watchEffect } from 'vue'
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'
import pinia from '~@/core/pinia'
import { useTelaLarga } from '~@/core/media'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { CHAVE_OVERLAY } from '~@/overlays/useOverlay'
import Encaixe from '~@/overlays/Encaixe.vue'

// 2. Composables
const store = useOverlayStore(pinia)
const larga = useTelaLarga()

// 3. Props & Emits
const props = defineProps({
  // Entrada que já existe no store. Sem ela, a moldura registra a própria.
  entradaId: {
    type: String,
    default: null
  },
  kind: {
    type: String,
    default: 'drawer'
  },
  type: {
    type: String,
    default: 'default'
  },
  // side, size, mode, modeEstreito, scrim, title
  opcoes: {
    type: Object,
    default: () => ({})
  },
  source: {
    type: String,
    default: 'local'
  },
  chave: {
    type: String,
    default: null
  },
  aberto: {
    type: Boolean,
    default: true
  }
})
const emit = defineEmits(['fechar', 'saiu'])

// 4. State & Refs
const TAMANHOS = ['sm', 'md', 'lg']
const conteudoEl = document.createElement('div')
const rodapeEl = document.createElement('div')
const tituloLocal = ref(props.opcoes.title || '')
const ordemLocal = ref(0)

const id = props.entradaId || store.registrar({
  kind: props.kind,
  type: props.type,
  opcoes: props.opcoes,
  source: props.source,
  chave: props.chave,
  modal: (props.opcoes.mode || 'overlay') === 'overlay',
  fechador: () => emit('fechar')
}).id
const idTitulo = `${id}-titulo`

// 5. Computed Properties
const entrada = computed(() => store.entrada(id))
const lado = computed(() => (props.opcoes.side === 'left' ? 'left' : 'right'))
const doca = computed(() => document.querySelector(`[data-v8-doca="${lado.value}"]`))
const modo = computed(() => {
  if (props.kind !== 'drawer') {
    return 'overlay'
  }
  const pedido = larga.value ? props.opcoes.mode : (props.opcoes.modeEstreito || props.opcoes.mode)
  if (pedido === 'push') {
    return 'push'
  }
  if (pedido === 'docked') {
    // Sem doca no layout (como no layout sem shell), o drawer abre por cima.
    return doca.value ? 'docked' : 'overlay'
  }
  return 'overlay'
})
const modal = computed(() => modo.value === 'overlay')
const comScrim = computed(() => props.opcoes.scrim !== false)
const titulo = computed(() => tituloLocal.value || (props.kind === 'drawer' ? 'Painel' : 'Diálogo'))
const papel = computed(() => (props.type === 'confirm' ? 'alertdialog' : 'dialog'))
const ehTopo = computed(() => store.ehTopo(id))
const tamanho = computed(() => props.opcoes.size || (props.type === 'confirm' ? 'sm' : 'md'))
const classeTamanho = computed(() => (TAMANHOS.includes(tamanho.value) ? `v8-tamanho-${tamanho.value}` : null))
const larguraCss = computed(() => (TAMANHOS.includes(tamanho.value) ? `var(--largura-${tamanho.value})` : tamanho.value))
// Um overlay aberto sobre um modal fica na camada do modal (V8-OVL-003).
const camada = computed(() => {
  if (props.kind === 'modal') {
    return 'v8-camada-modal'
  }
  const pilha = store.pilha
  const posicao = pilha.findIndex(e => e.id === id)
  const abaixo = posicao === -1 ? pilha : pilha.slice(0, posicao)
  return abaixo.some(e => e.kind === 'modal') ? 'v8-camada-modal' : 'v8-camada-drawer'
})
const estiloOrdem = computed(() => ({ '--v8-ordem': ordemLocal.value }))
const estilo = computed(() => {
  const css = { '--v8-ordem': ordemLocal.value, '--v8-profundidade': store.profundidade(id) }
  if (!classeTamanho.value && tamanho.value !== 'fullscreen') {
    css['--v8-largura'] = tamanho.value
  }
  return css
})
const classesModal = computed(() => {
  const classes = ['v8-overlay', camada.value, classeTamanho.value]
  if (props.kind === 'drawer') {
    classes.push('v8-drawer', `v8-drawer-${lado.value}`)
  } else {
    classes.push('v8-modal')
    if (props.type === 'fullscreen' || tamanho.value === 'fullscreen') {
      classes.push('v8-modal-fullscreen')
    }
  }
  return classes
})
const classesLateral = computed(() => [
  'v8-lateral',
  `v8-lateral-${modo.value}`,
  `v8-lateral-${lado.value}`,
  classeTamanho.value
])
const transicao = computed(() => (props.kind === 'drawer' ? `v8-t-drawer-${lado.value}` : 'v8-t-modal'))

// 6. Watchers
// Guarda o último título e a última ordem: a moldura ainda é desenhada enquanto sai da tela,
// quando a entrada já deixou o store.
watch(entrada, valor => {
  if (valor) {
    tituloLocal.value = valor.titulo
    ordemLocal.value = store.ordem(id)
  }
}, { immediate: true, deep: true })

watch(() => store.entradas.length, () => {
  if (entrada.value) {
    ordemLocal.value = store.ordem(id)
  }
})

watch(modal, valor => store.setModal(id, valor), { immediate: true })

// Em `push` o conteúdo da página se desloca pela largura do drawer.
watchEffect(aoLimpar => {
  if (modo.value !== 'push' || !props.aberto) {
    return
  }
  const variavel = `--v8-empurra-${lado.value}`
  document.documentElement.style.setProperty(variavel, `min(${larguraCss.value}, 100vw)`)
  aoLimpar(() => document.documentElement.style.removeProperty(variavel))
})

// 7. Events & Lifecycle Hooks
provide(CHAVE_OVERLAY, {
  id,
  rodapeEl,
  close: valor => store.close(id, valor),
  dismiss: () => store.requestClose(id),
  setDirty: valor => store.setDirty(id, valor),
  setTitle: valor => store.setTitle(id, valor)
})

onBeforeUnmount(() => {
  if (!props.entradaId) {
    store.remover(id)
  }
})

// 8. Functions
function pedirFechamento() {
  return store.requestClose(id)
}

// O Reka pede para fechar por ESC ou clique fora, e só no overlay do topo (V8-OVL-011).
function aoMudarAberto(valor) {
  if (!valor) {
    pedirFechamento()
  }
}

// Interagir com um toast não conta como clique fora do overlay.
function aoInteragirFora(evento) {
  const alvo = evento.detail?.originalEvent?.target || evento.target
  if (alvo?.closest?.('.v8-toasts')) {
    evento.preventDefault()
  }
}
</script>
