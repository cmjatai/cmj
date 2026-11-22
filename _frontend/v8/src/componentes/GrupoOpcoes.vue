<template>
  <RadioGroupRoot
    v-model="valor"
    class="v8-opcoes"
    :name="name || undefined"
    :disabled="disabled"
    :orientation="orientacao"
    :aria-label="rotulo || undefined"
    :data-orientacao="orientacao"
  >
    <label
      v-for="opcao in opcoes"
      :key="opcao.valor"
      class="v8-opcao-rotulo"
    >
      <RadioGroupItem
        class="v8-opcao"
        :value="opcao.valor"
        :disabled="opcao.desabilitado"
      >
        <RadioGroupIndicator class="v8-opcao-marca" />
      </RadioGroupItem>
      <span>{{ opcao.rotulo }}</span>
    </label>
  </RadioGroupRoot>
</template>

<script setup>
// Grupo de opções (docs/specs/v8/componentes.md): uma opção entre várias, sobre o RadioGroup do
// Reka UI. As setas do teclado trocam a opção. Com `name`, dentro de um <form>, vai no envio
// nativo. Cada opção é `{ valor, rotulo, desabilitado }`.
//
//   <GrupoOpcoes v-model="turno" name="turno" rotulo="Turno" :opcoes="turnos" />

// 1. Imports
import { RadioGroupIndicator, RadioGroupItem, RadioGroupRoot } from 'reka-ui'

// 3. Props & Emits
defineProps({
  opcoes: {
    type: Array,
    required: true
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
  },
  orientacao: {
    type: String,
    default: 'vertical'
  }
})
const valor = defineModel({ type: String, default: undefined })
</script>
