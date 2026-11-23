<template>
  <Separator
    class="v8-separador"
    :orientation="orientacao"
    :decorative="decorativo"
  />
</template>

<script setup>
// Separador (docs/specs/v8/componentes.md), sobre o Separator do Reka UI: linha entre conteúdos.
// `decorativo` tira o separador da árvore de acessibilidade.
//
//   <Separador orientacao="vertical" decorativo />

// 1. Imports
import { Separator } from 'reka-ui'

// 3. Props & Emits
defineProps({
  orientacao: {
    type: String,
    default: 'horizontal'
  },
  decorativo: {
    type: Boolean,
    default: false
  }
})
</script>
