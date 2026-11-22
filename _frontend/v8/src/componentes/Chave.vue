<template>
  <label class="v8-chave-rotulo">
    <SwitchRoot
      :id="id || undefined"
      v-model="ligada"
      class="v8-chave"
      :name="name || undefined"
      :disabled="disabled"
    >
      <SwitchThumb class="v8-chave-pino" />
    </SwitchRoot>
    <span><slot>{{ rotulo }}</slot></span>
  </label>
</template>

<script setup>
// Chave liga e desliga (docs/specs/v8/componentes.md), sobre o Switch do Reka UI. Com `name`,
// dentro de um <form>, vai no envio nativo.
//
//   <Chave v-model="avisar" name="avisar" rotulo="Avisar por e-mail" />

// 1. Imports
import { SwitchRoot, SwitchThumb } from 'reka-ui'

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
const ligada = defineModel({ type: Boolean, default: false })
</script>
