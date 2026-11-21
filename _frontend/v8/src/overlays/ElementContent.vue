<template>
  <div ref="raiz">
    <p
      v-if="ausente"
      class="v8-overlay-estado"
      role="alert"
    >
      O conteúdo deste painel não está na página.
    </p>
  </div>
</template>
<script setup>
// Usa como conteúdo um elemento que o Django já pôs na página: ele é movido para o overlay ao
// abrir e devolvido ao lugar de origem ao fechar (V8-OVL-043).

// 1. Imports
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useOverlay } from '~@/overlays/useOverlay'

// 2. Composables
const store = useOverlayStore(pinia)
const overlay = useOverlay()

// 3. Props & Emits
const props = defineProps({
  idElemento: {
    type: String,
    required: true
  }
})

// 4. State & Refs
const raiz = ref(null)
const ausente = ref(false)
let elemento = null
let marcador = null

// 5. Computed Properties
// 6. Watchers
// O elemento volta ao lugar assim que o overlay fecha, sem esperar a animação de saída.
watch(() => store.entrada(overlay.id), entrada => {
  if (!entrada) {
    devolver()
  }
})

// 7. Events & Lifecycle Hooks
onMounted(() => {
  elemento = document.getElementById(props.idElemento)
  if (!elemento) {
    ausente.value = true
    return
  }
  marcador = document.createComment(`v8-origem:${props.idElemento}`)
  elemento.before(marcador)
  raiz.value.append(elemento)
})

onBeforeUnmount(devolver)

// 8. Functions
function devolver() {
  if (elemento && marcador?.parentNode) {
    marcador.replaceWith(elemento)
  }
  elemento = null
  marcador = null
}
</script>
