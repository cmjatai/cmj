<template>
  <ColorAreaRoot
    v-slot="{ style }"
    v-model="cor"
    class="v8-area-cor"
    color-space="hsb"
    x-channel="saturation"
    y-channel="brightness"
    :disabled="disabled"
  >
    <ColorAreaArea
      class="v8-area-cor-plano"
      :style="style"
      :aria-label="rotulo || 'Saturação e brilho'"
      aria-roledescription="seletor de cor"
    >
      <ColorAreaThumb
        class="v8-area-cor-pino"
        aria-roledescription="marcador de cor"
      />
    </ColorAreaArea>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="cor"
    >
  </ColorAreaRoot>
</template>

<script setup>
// Área de cor (docs/specs/v8/componentes.md), sobre o ColorArea do Reka UI: saturação na
// horizontal e brilho na vertical, no espaço HSB. Para o matiz, use junto um `DeslizanteCor`
// com o mesmo v-model. O v-model é a cor em hexadecimal.
//
//   <AreaCor v-model="cor" name="cor" />
//   <DeslizanteCor v-model="cor" canal="hue" />

// 1. Imports
import { ColorAreaArea, ColorAreaRoot, ColorAreaThumb } from 'reka-ui'

// 3. Props & Emits
defineProps({
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
</script>
