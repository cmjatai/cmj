<template>
  <ToggleGroupRoot
    v-model="valor"
    class="v8-grupo-alternadores"
    :type="multiplo ? 'multiple' : 'single'"
    :name="name || undefined"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <ToggleGroupItem
      v-for="item in itens"
      :key="item.valor"
      class="v8-btn v8-alternador"
      :value="item.valor"
      :disabled="item.desabilitado"
      :aria-label="item.rotuloAcessivel || undefined"
    >
      {{ item.rotulo }}
    </ToggleGroupItem>
  </ToggleGroupRoot>
</template>

<script setup>
// Grupo de alternadores (docs/specs/v8/componentes.md), sobre o ToggleGroup do Reka UI: um
// valor (ou vários, com `multiplo`) entre botões lado a lado. Cada item é
// `{ valor, rotulo, desabilitado, rotuloAcessivel }`.
//
//   <GrupoAlternadores v-model="alinhamento" name="alinhamento" rotulo="Alinhamento" :itens="itens" />

// 1. Imports
import { ToggleGroupItem, ToggleGroupRoot } from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  multiplo: {
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
const valor = defineModel({ type: [String, Array], default: undefined })
</script>
