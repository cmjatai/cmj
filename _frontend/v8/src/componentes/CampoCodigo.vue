<template>
  <PinInputRoot
    :id="id || undefined"
    v-model="digitos"
    class="v8-campo-codigo"
    :type="numerico ? 'number' : 'text'"
    :mask="mascarar"
    :otp="otp"
    :name="name || undefined"
    :disabled="disabled"
    @complete="lista => emit('completo', lista.join(''))"
  >
    <PinInputInput
      v-for="(_, posicao) in tamanho"
      :key="posicao"
      class="v8-entrada v8-campo-codigo-casa"
      :index="posicao"
      :aria-label="`${rotulo || 'Código'}, posição ${posicao + 1} de ${tamanho}`"
    />
  </PinInputRoot>
</template>

<script setup>
// Campo de código (docs/specs/v8/componentes.md), sobre o PinInput do Reka UI: uma casa por
// caractere, para códigos de verificação. O v-model é o código inteiro, em texto.
//
//   <CampoCodigo v-model="codigo" name="codigo" :tamanho="6" numerico otp @completo="validar" />

// 1. Imports
import { computed } from 'vue'
import { PinInputInput, PinInputRoot } from 'reka-ui'

// 3. Props & Emits
const props = defineProps({
  tamanho: {
    type: Number,
    default: 6
  },
  numerico: {
    type: Boolean,
    default: false
  },
  mascarar: {
    type: Boolean,
    default: false
  },
  otp: {
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
  id: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const emit = defineEmits(['completo'])
const codigo = defineModel({ type: String, default: '' })

// 5. Computed Properties
// O Reka guarda uma lista com um caractere por casa.
const digitos = computed({
  get: () => {
    const caracteres = [...String(codigo.value ?? '')].slice(0, props.tamanho)
    return props.numerico ? caracteres.map(Number) : caracteres
  },
  set: lista => {
    codigo.value = lista.map(c => (c === undefined || c === null ? '' : String(c))).join('')
  }
})
</script>
