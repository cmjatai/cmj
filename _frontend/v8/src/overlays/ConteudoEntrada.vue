<template>
  <ModalConfirm
    v-if="conteudo?.confirm"
    v-bind="opcoes"
  />
  <FragmentContent
    v-else-if="conteudo?.frag"
    :caminho="conteudo.frag"
  />
  <ElementContent
    v-else-if="conteudo?.el"
    :id-elemento="conteudo.el"
  />
  <component
    :is="componente"
    v-else-if="componente"
    v-bind="conteudo.props || {}"
  />
  <div
    v-else-if="erro"
    class="v8-overlay-estado"
    role="alert"
  >
    <p>Não foi possível carregar este conteúdo.</p>
    <button
      type="button"
      class="v8-btn"
      @click="carregar"
    >
      Tentar de novo
    </button>
  </div>
  <div
    v-else
    class="v8-overlay-estado"
    role="status"
  >
    Carregando…
  </div>
</template>
<script setup>
// Escolhe o que desenhar dentro de um overlay aberto pelo store: confirm, fragmento, elemento da
// página ou componente importado sob demanda (V8-OVL-040 e 041).

// 1. Imports
import { markRaw, onMounted, shallowRef, ref } from 'vue'
import ModalConfirm from '~@/overlays/ModalConfirm.vue'
import FragmentContent from '~@/overlays/FragmentContent.vue'
import ElementContent from '~@/overlays/ElementContent.vue'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  conteudo: {
    type: Object,
    default: null
  },
  opcoes: {
    type: Object,
    default: () => ({})
  }
})

// 4. State & Refs
const componente = shallowRef(null)
const erro = ref(false)

// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
onMounted(carregar)

// 8. Functions
function ehCarregador(valor) {
  return typeof valor === 'function' && !valor.render && !valor.setup && !valor.__vccOpts
}

async function carregar() {
  const alvo = props.conteudo?.componente
  if (!alvo) {
    return
  }
  erro.value = false
  if (!ehCarregador(alvo)) {
    componente.value = markRaw(alvo)
    return
  }
  try {
    const modulo = await alvo()
    componente.value = markRaw(modulo.default || modulo)
  } catch (falha) {
    console.error('Falha ao carregar o conteúdo do overlay.', falha)
    erro.value = true
  }
}
</script>
