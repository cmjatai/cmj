<template>
  <DateFieldRoot
    :id="id || undefined"
    v-slot="{ segments }"
    v-model="valor"
    class="v8-entrada v8-campo-data"
    :locale="IDIOMA"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <template
      v-for="segmento in segments"
      :key="segmento.part"
    >
      <DateFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </DateFieldInput>
      <DateFieldInput
        v-else
        :part="segmento.part"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </DateFieldInput>
    </template>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="texto"
    >
  </DateFieldRoot>
</template>

<script setup>
// Campo de data (docs/specs/v8/componentes.md), sobre o DateField do Reka UI: a data é digitada
// por partes (dia, mês e ano), em pt-BR, e as setas mudam cada parte. O v-model é AAAA-MM-DD.
//
//   <CampoData v-model="nascimento" name="nascimento" rotulo="Nascimento" />

// 1. Imports
import { computed } from 'vue'
import { DateFieldInput, DateFieldRoot } from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, dia } from '~@/componentes/datas'

// 3. Props & Emits
defineProps({
  id: {
    type: String,
    default: ''
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
const FORMATO = dia
const texto = defineModel({ type: String, default: '' })

// 5. Computed Properties
// O v-model é texto ISO; o Reka trabalha com objetos de data (datas.js).
const valor = computed({
  get: () => FORMATO.paraObjeto(texto.value),
  set: objeto => {
    texto.value = FORMATO.paraTexto(objeto)
  }
})
</script>
