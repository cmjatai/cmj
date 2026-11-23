<template>
  <ScrollAreaRoot
    class="v8-area-rolagem"
    :type="tipo"
  >
    <ScrollAreaViewport
      class="v8-area-rolagem-janela"
      :aria-label="rotulo || undefined"
    >
      <slot />
    </ScrollAreaViewport>
    <ScrollAreaScrollbar
      class="v8-area-rolagem-barra"
      orientation="vertical"
    >
      <ScrollAreaThumb class="v8-area-rolagem-pino" />
    </ScrollAreaScrollbar>
    <ScrollAreaScrollbar
      class="v8-area-rolagem-barra"
      orientation="horizontal"
    >
      <ScrollAreaThumb class="v8-area-rolagem-pino" />
    </ScrollAreaScrollbar>
    <ScrollAreaCorner />
  </ScrollAreaRoot>
</template>

<script setup>
// Área de rolagem (docs/specs/v8/componentes.md), sobre o ScrollArea do Reka UI: rolagem nativa
// com a barra no visual do tema. A altura vem de quem usa, por classe (por exemplo `h-64`).
//
//   <AreaRolagem class="h-64" rotulo="Histórico">...</AreaRolagem>

// 1. Imports
import { ScrollAreaCorner, ScrollAreaRoot, ScrollAreaScrollbar, ScrollAreaThumb, ScrollAreaViewport } from 'reka-ui'

// 3. Props & Emits
defineProps({
  // `hover`, `scroll`, `auto` ou `always`.
  tipo: {
    type: String,
    default: 'hover'
  },
  rotulo: {
    type: String,
    default: ''
  }
})
</script>
