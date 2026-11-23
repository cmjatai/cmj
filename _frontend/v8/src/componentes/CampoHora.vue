<template>
  <TimeFieldRoot
    :id="id || undefined"
    v-slot="{ segments }"
    v-model="valor"
    class="v8-entrada v8-campo-data"
    :locale="IDIOMA"
    :hour-cycle="24"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <template
      v-for="segmento in segments"
      :key="segmento.part"
    >
      <TimeFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </TimeFieldInput>
      <TimeFieldInput
        v-else
        :part="segmento.part"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </TimeFieldInput>
    </template>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="texto"
    >
  </TimeFieldRoot>
</template>

<script setup>
// Campo de hora (docs/specs/v8/componentes.md), sobre o TimeField do Reka UI: horas e minutos
// digitados por partes, no relógio de 24 horas. O v-model é HH:MM.
//
//   <CampoHora v-model="inicio" name="inicio" rotulo="Início" />

// 1. Imports
import { computed } from 'vue'
import { TimeFieldInput, TimeFieldRoot } from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, hora } from '~@/componentes/datas'

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
const FORMATO = hora
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
