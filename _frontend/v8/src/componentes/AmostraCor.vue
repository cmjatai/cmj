<template>
  <ColorSwatch
    class="v8-amostra-cor"
    :data-tamanho="tamanho"
    :color="cor"
    :label="rotulo || cor || 'Sem cor'"
    aria-roledescription="amostra de cor"
  />
</template>

<script setup>
// Amostra de cor (docs/specs/v8/componentes.md), sobre o ColorSwatch do Reka UI. O nome acessível
// é o `rotulo`, ou o próprio código da cor.
//
//   <AmostraCor :cor="partido.cor" :rotulo="partido.sigla" />

// 1. Imports
import { ColorSwatch } from 'reka-ui'

// 3. Props & Emits
defineProps({
  cor: {
    type: String,
    default: ''
  },
  rotulo: {
    type: String,
    default: ''
  },
  // `sm`, `md` ou `lg`.
  tamanho: {
    type: String,
    default: 'md'
  }
})
</script>
