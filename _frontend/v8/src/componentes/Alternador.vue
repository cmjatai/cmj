<template>
  <Toggle
    v-model="pressionado"
    v-bind="$attrs"
    class="v8-btn v8-alternador"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <slot>{{ texto }}</slot>
  </Toggle>
  <input
    v-if="name && pressionado && !disabled"
    type="hidden"
    :name="name"
    :value="value"
  >
</template>

<script setup>
// Alternador (docs/specs/v8/componentes.md): botão que fica pressionado, sobre o Toggle do Reka
// UI. Com `name`, vai no formulário como uma caixa de marcação: o `value` só quando pressionado.
// O campo oculto é do próprio componente, porque o do Toggle nunca fica marcado (D6).
//
//   <Alternador v-model="negrito" name="negrito" rotulo="Negrito">N</Alternador>

// 1. Imports
import { Toggle } from 'reka-ui'

// 3. Props & Emits
// Os atributos vão para o botão, e não para o campo oculto ao lado dele.
defineOptions({ inheritAttrs: false })
defineProps({
  texto: {
    type: String,
    default: ''
  },
  // Nome acessível, quando o conteúdo é só um ícone.
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
  disabled: {
    type: Boolean,
    default: false
  }
})
const pressionado = defineModel({ type: Boolean, default: false })
</script>
