<template>
  <div
    v-if="erro"
    class="v8-overlay-estado"
    role="alert"
  >
    <p>{{ erro.mensagem || 'Não foi possível carregar os dados.' }}</p>
    <button
      v-if="erro.codigo !== 'nao_encontrado'"
      type="button"
      class="v8-btn"
      @click="emit('tentar')"
    >
      Tentar de novo
    </button>
  </div>
  <div
    v-else-if="carregando"
    class="v8-overlay-estado"
    role="status"
  >
    Carregando…
  </div>
</template>
<script setup>
// Estado de carregamento ou de falha de uma tela da demo, com a opção de tentar de novo.
// `erro` é o HttpError da tentativa. O que não foi encontrado não oferece nova tentativa.

// 1. Imports
// 2. Composables
// 3. Props & Emits
defineProps({
  carregando: {
    type: Boolean,
    default: false
  },
  erro: {
    type: Object,
    default: null
  }
})
const emit = defineEmits(['tentar'])

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
