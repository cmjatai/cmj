<template>
  <SplitterGroup
    class="v8-divisor"
    :direction="direcao"
  >
    <SplitterPanel
      class="v8-divisor-painel"
      :default-size="tamanhos[0]"
      :min-size="minimo"
    >
      <slot name="primeiro" />
    </SplitterPanel>
    <SplitterResizeHandle
      class="v8-divisor-alca"
      :aria-label="rotulo"
    />
    <SplitterPanel
      class="v8-divisor-painel"
      :default-size="tamanhos[1]"
      :min-size="minimo"
    >
      <slot name="segundo" />
    </SplitterPanel>
  </SplitterGroup>
</template>

<script setup>
// Divisor (docs/specs/v8/componentes.md), sobre o Splitter do Reka UI: dois painéis separados por
// uma alça que se arrasta, ou se move pelas setas do teclado. Os tamanhos são em porcentagem.
//
//   <Divisor :tamanhos="[30, 70]"><template #primeiro>...</template><template #segundo>...</template></Divisor>

// 1. Imports
import { SplitterGroup, SplitterPanel, SplitterResizeHandle } from 'reka-ui'

// 3. Props & Emits
defineProps({
  direcao: {
    type: String,
    default: 'horizontal'
  },
  tamanhos: {
    type: Array,
    default: () => [50, 50]
  },
  // Tamanho mínimo de cada painel, em porcentagem.
  minimo: {
    type: Number,
    default: 15
  },
  rotulo: {
    type: String,
    default: 'Redimensionar painéis'
  }
})
</script>
