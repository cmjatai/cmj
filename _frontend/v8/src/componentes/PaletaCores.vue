<template>
  <ColorSwatchPickerRoot
    v-model="cor"
    class="v8-paleta-cores"
    :multiple="multipla"
    :name="name || undefined"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <ColorSwatchPickerItem
      v-for="opcao in opcoes"
      :key="opcao.valor"
      class="v8-paleta-cores-item"
      :value="opcao.valor"
      :aria-label="opcao.rotulo || opcao.valor"
    >
      <ColorSwatchPickerItemSwatch
        class="v8-amostra-cor"
        aria-roledescription="amostra de cor"
      />
      <ColorSwatchPickerItemIndicator class="v8-paleta-cores-marca">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="ICONES.marca" />
        </svg>
      </ColorSwatchPickerItemIndicator>
    </ColorSwatchPickerItem>
  </ColorSwatchPickerRoot>
</template>

<script setup>
// Paleta de cores (docs/specs/v8/componentes.md), sobre o ColorSwatchPicker do Reka UI: escolha
// entre cores prontas. Cada opção é `{ valor, rotulo }`, com `valor` em hexadecimal; o v-model é
// a cor escolhida (ou a lista, com `multipla`).
//
//   <PaletaCores v-model="cor" name="cor" rotulo="Cor" :opcoes="cores" />

// 1. Imports
import {
  ColorSwatchPickerItem,
  ColorSwatchPickerItemIndicator,
  ColorSwatchPickerItemSwatch,
  ColorSwatchPickerRoot
} from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  opcoes: {
    type: Array,
    required: true
  },
  multipla: {
    type: Boolean,
    default: false
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
const cor = defineModel({ type: [String, Array], default: undefined })
</script>
