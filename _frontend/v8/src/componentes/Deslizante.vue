<template>
  <SliderRoot
    v-model="valores"
    class="v8-deslizante"
    :min="min"
    :max="max"
    :step="passo"
    :name="name || undefined"
    :disabled="disabled"
  >
    <SliderTrack class="v8-deslizante-trilho">
      <SliderRange class="v8-deslizante-faixa" />
    </SliderTrack>
    <SliderThumb
      v-for="(_, posicao) in valores"
      :key="posicao"
      class="v8-deslizante-pino"
      :aria-label="rotuloDoPino(posicao)"
    />
  </SliderRoot>
</template>

<script setup>
// Controle deslizante (docs/specs/v8/componentes.md), sobre o Slider do Reka UI. O v-model é um
// número; com uma lista de dois números, o controle marca um intervalo, com um pino em cada ponta.
//
//   <Deslizante v-model="volume" name="volume" rotulo="Volume" :max="10" />

// 1. Imports
import { computed } from 'vue'
import { SliderRange, SliderRoot, SliderThumb, SliderTrack } from 'reka-ui'

// 3. Props & Emits
const props = defineProps({
  min: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    default: 100
  },
  passo: {
    type: Number,
    default: 1
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
const valor = defineModel({ type: [Number, Array], default: 0 })

// 5. Computed Properties
// O Reka trabalha sempre com uma lista; o v-model segue o formato que recebeu.
const valores = computed({
  get: () => (Array.isArray(valor.value) ? valor.value : [valor.value ?? props.min]),
  set: lista => {
    valor.value = Array.isArray(valor.value) ? lista : lista[0]
  }
})

// 8. Functions
function rotuloDoPino(posicao) {
  if (valores.value.length < 2) {
    return props.rotulo || undefined
  }
  const ponta = posicao === 0 ? 'mínimo' : 'máximo'
  return props.rotulo ? `${props.rotulo}, ${ponta}` : ponta
}
</script>
