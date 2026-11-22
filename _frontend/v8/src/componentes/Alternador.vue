<template>
  <Toggle
    v-model="pressionado"
    class="v8-btn v8-alternador"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <slot>{{ texto }}</slot>
  </Toggle>
</template>

<script setup>
// Alternador (docs/specs/v8/componentes.md): botão que fica pressionado, sobre o Toggle do Reka
// UI. Não participa do envio nativo de formulário: guarde o valor pelo v-model.
//
//   <Alternador v-model="negrito" rotulo="Negrito">N</Alternador>

// 1. Imports
import { Toggle } from 'reka-ui'

// 3. Props & Emits
defineProps({
  texto: {
    type: String,
    default: ''
  },
  // Nome acessível, quando o conteúdo é só um ícone.
  rotulo: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const pressionado = defineModel({ type: Boolean, default: false })
</script>
