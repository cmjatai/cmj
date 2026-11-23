<template>
  <HoverCardRoot
    v-model:open="aberto"
    :open-delay="atraso"
    :close-delay="200"
  >
    <HoverCardTrigger as-child>
      <slot name="gatilho" />
    </HoverCardTrigger>
    <HoverCardPortal>
      <HoverCardContent
        class="v8-cartao-flutuante"
        :side="lado"
        :side-offset="6"
      >
        <slot />
        <HoverCardArrow
          class="v8-popover-seta"
          :width="12"
          :height="6"
        />
      </HoverCardContent>
    </HoverCardPortal>
  </HoverCardRoot>
</template>

<script setup>
// Cartão flutuante (docs/specs/v8/componentes.md), sobre o HoverCard do Reka UI: uma prévia que
// aparece ao passar o mouse ou focar o gatilho, em geral um link. Não substitui a página do link.
//
//   <CartaoFlutuante>
//     <template #gatilho><a href="/v8/...">Vereadora Exemplo</a></template>
//     ...prévia...
//   </CartaoFlutuante>

// 1. Imports
import { HoverCardArrow, HoverCardContent, HoverCardPortal, HoverCardRoot, HoverCardTrigger } from 'reka-ui'

// 3. Props & Emits
defineProps({
  lado: {
    type: String,
    default: 'bottom'
  },
  // Espera antes de abrir, em milissegundos.
  atraso: {
    type: Number,
    default: 500
  }
})
const aberto = defineModel('open', { type: Boolean, default: false })
</script>
