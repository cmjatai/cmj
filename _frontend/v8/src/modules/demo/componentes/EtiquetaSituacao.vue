<template>
  <span :class="['v8-etiqueta', situacao === 'ativo' ? 'v8-etiqueta-ok' : 'v8-etiqueta-neutra']">
    {{ rotuloDaSituacao(situacao) }}
  </span>
</template>
<script setup>
// Etiqueta da situação do cliente, igual à que o Django desenha na página da demo.

// 1. Imports
import { rotuloDaSituacao } from '~@/modules/demo/formatos'

// 2. Composables
// 3. Props & Emits
defineProps({
  situacao: {
    type: String,
    default: ''
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
