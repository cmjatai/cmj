<template>
  <ColorFieldRoot
    v-model="cor"
    class="v8-campo-cor"
    :name="name || undefined"
    :disabled="disabled"
  >
    <ColorSwatch
      class="v8-amostra-cor"
      :color="cor || ''"
      :label="cor || 'Sem cor'"
      aria-roledescription="amostra de cor"
    />
    <ColorFieldInput
      :id="id || undefined"
      class="v8-entrada v8-campo-cor-entrada"
      :aria-label="rotulo || undefined"
    />
  </ColorFieldRoot>
</template>

<script setup>
// Campo de cor (docs/specs/v8/componentes.md), sobre o ColorField e o ColorSwatch do Reka UI: a
// cor digitada em hexadecimal, com a amostra ao lado. O valor só vale ao sair do campo ou com
// Enter; texto inválido volta ao anterior.
//
//   <CampoCor v-model="cor" name="cor" rotulo="Cor da etiqueta" />

// 1. Imports
import { ColorFieldInput, ColorFieldRoot, ColorSwatch } from 'reka-ui'

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
  id: {
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
