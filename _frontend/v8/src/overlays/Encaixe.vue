<template>
  <div
    ref="raiz"
    class="v8-encaixe"
  />
</template>
<script setup>
// Recebe um nó que já existe e o mantém dentro de si. É o que permite trocar a moldura de um
// overlay (modal, lateral) sem recriar o conteúdo (V8-OVL-033).

// 1. Imports
import { onMounted, ref, watch } from 'vue'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  el: {
    type: Object,
    default: null
  }
})

// 4. State & Refs
const raiz = ref(null)

// 5. Computed Properties
// 6. Watchers
watch(() => props.el, encaixar)

// 7. Events & Lifecycle Hooks
onMounted(encaixar)

// 8. Functions
function encaixar() {
  if (raiz.value && props.el && props.el.parentNode !== raiz.value) {
    raiz.value.replaceChildren(props.el)
  }
}
</script>
