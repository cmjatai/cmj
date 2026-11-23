<template>
  <AspectRatio
    class="v8-proporcao"
    :ratio="proporcao"
  >
    <slot />
  </AspectRatio>
</template>

<script setup>
// Caixa com proporção fixa (docs/specs/v8/componentes.md), sobre o AspectRatio do Reka UI, para
// imagens e vídeos. `proporcao` é largura sobre altura.
//
//   <Proporcao :proporcao="16 / 9"><iframe ... /></Proporcao>

// 1. Imports
import { AspectRatio } from 'reka-ui'

// 3. Props & Emits
defineProps({
  proporcao: {
    type: Number,
    default: 16 / 9
  }
})
</script>
