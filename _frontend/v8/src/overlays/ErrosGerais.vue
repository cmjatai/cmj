<template>
  <div
    v-if="mensagens.length"
    class="v8-alerta v8-alerta-erro"
    role="alert"
  >
    <ul>
      <li
        v-for="(mensagem, i) in mensagens"
        :key="i"
      >
        {{ mensagem }}
      </li>
    </ul>
  </div>
</template>
<script setup>
// Erros que não pertencem a um campo, no topo do formulário (V8-OVL-064).

// 1. Imports
// 2. Composables
// 3. Props & Emits
defineProps({
  mensagens: {
    type: Array,
    default: () => []
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
