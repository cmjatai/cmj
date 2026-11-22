<template>
  <label class="v8-caixa-rotulo">
    <CheckboxRoot
      :id="id || undefined"
      v-model="marcado"
      class="v8-caixa"
      :name="name || undefined"
      :value="value"
      :disabled="disabled"
    >
      <CheckboxIndicator class="v8-caixa-marca">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path
            v-if="marcado === 'indeterminate'"
            d="M6 12h12"
          />
          <path
            v-else
            d="M5 12l5 5 9-10"
          />
        </svg>
      </CheckboxIndicator>
    </CheckboxRoot>
    <span><slot>{{ rotulo }}</slot></span>
  </label>
</template>

<script setup>
// Caixa de marcação (docs/specs/v8/componentes.md), sobre o Checkbox do Reka UI. O v-model é
// `true`, `false` ou `'indeterminate'`. Com `name`, dentro de um <form>, vai no envio nativo.
//
//   <CaixaMarcacao v-model="aceito" name="aceito" rotulo="Aceito os termos" />

// 1. Imports
import { CheckboxIndicator, CheckboxRoot } from 'reka-ui'

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
  value: {
    type: String,
    default: 'on'
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
const marcado = defineModel({ type: [Boolean, String], default: false })
</script>
