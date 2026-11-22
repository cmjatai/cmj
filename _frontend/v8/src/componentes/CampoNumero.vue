<template>
  <NumberFieldRoot
    :id="id || undefined"
    v-model="numero"
    class="v8-campo-numero"
    :min="min"
    :max="max"
    :step="passo"
    :format-options="formato"
    :locale="locale"
    :name="name || undefined"
    :disabled="disabled"
    :readonly="readonly"
  >
    <NumberFieldDecrement
      class="v8-campo-numero-botao"
      aria-label="Diminuir"
    >
      <svg
        class="v8-icone"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        aria-hidden="true"
      >
        <path :d="ICONES.menos" />
      </svg>
    </NumberFieldDecrement>
    <NumberFieldInput
      class="v8-campo-numero-entrada"
      :aria-label="rotulo || undefined"
    />
    <NumberFieldIncrement
      class="v8-campo-numero-botao"
      aria-label="Aumentar"
    >
      <svg
        class="v8-icone"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        aria-hidden="true"
      >
        <path :d="ICONES.mais" />
      </svg>
    </NumberFieldIncrement>
  </NumberFieldRoot>
</template>

<script setup>
// Campo de número (docs/specs/v8/componentes.md), sobre o NumberField do Reka UI, com botões de
// mais e menos e o número formatado no idioma da página (pt-BR). O valor só é aplicado ao sair do
// campo ou com Enter; no formulário vai o número cru, sem formatação.
//
//   <CampoNumero v-model="valor" name="valor" :formato="{ style: 'currency', currency: 'BRL' }" />

// 1. Imports
import { NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput, NumberFieldRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  min: {
    type: Number,
    default: undefined
  },
  max: {
    type: Number,
    default: undefined
  },
  passo: {
    type: Number,
    default: 1
  },
  // Opções de Intl.NumberFormat, como moeda ou casas decimais.
  formato: {
    type: Object,
    default: undefined
  },
  locale: {
    type: String,
    default: 'pt-BR'
  },
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
  },
  readonly: {
    type: Boolean,
    default: false
  }
})
const numero = defineModel({ type: Number, default: undefined })
</script>
