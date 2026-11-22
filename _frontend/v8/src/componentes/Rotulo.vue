<template>
  <Label
    class="v8-rotulo"
    :for="para || undefined"
  >
    <slot>{{ texto }}</slot>
  </Label>
</template>

<script setup>
// Rótulo de campo (docs/specs/v8/componentes.md), sobre o Label do Reka UI, com o visual de
// `v8-rotulo`. Use `para` com o `id` do campo.
//
//   <Rotulo para="nome">Nome</Rotulo>

// 1. Imports
import { Label } from 'reka-ui'

// 3. Props & Emits
defineProps({
  para: {
    type: String,
    default: ''
  },
  texto: {
    type: String,
    default: ''
  }
})
</script>
