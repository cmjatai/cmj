<template>
  <ColorSliderRoot
    v-model="cor"
    class="v8-deslizante v8-deslizante-cor"
    color-space="hsb"
    :channel="canal"
    :name="name || undefined"
    :disabled="disabled"
  >
    <ColorSliderTrack class="v8-deslizante-cor-trilho" />
    <ColorSliderThumb
      class="v8-deslizante-pino"
      :aria-label="rotulo || NOMES_DOS_CANAIS[canal] || canal"
    />
  </ColorSliderRoot>
</template>

<script setup>
// Deslizante de cor (docs/specs/v8/componentes.md), sobre o ColorSlider do Reka UI: um canal da
// cor numa faixa com o gradiente dele. O v-model é a cor em hexadecimal.
//
//   <DeslizanteCor v-model="cor" canal="hue" />

// 1. Imports
import { ColorSliderRoot, ColorSliderThumb, ColorSliderTrack } from 'reka-ui'

// 3. Props & Emits
defineProps({
  // `hue`, `saturation`, `brightness` ou `alpha`.
  canal: {
    type: String,
    default: 'hue'
  },
  rotulo: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const cor = defineModel({ type: String, default: undefined })

// 4. State & Refs
const NOMES_DOS_CANAIS = {
  hue: 'Matiz',
  saturation: 'Saturação',
  brightness: 'Brilho',
  alpha: 'Opacidade'
}
</script>
