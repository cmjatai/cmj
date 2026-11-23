<template>
  <TimeRangeFieldRoot
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
      v-for="segmento in segments.start"
      :key="segmento.part"
    >
      <TimeRangeFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        :type="'start'"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </TimeRangeFieldInput>
      <TimeRangeFieldInput
        v-else
        :part="segmento.part"
        :type="'start'"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </TimeRangeFieldInput>
    </template>
    <span
      class="v8-campo-data-literal"
      aria-hidden="true"
    >–</span>
    <template
      v-for="segmento in segments.end"
      :key="segmento.part"
    >
      <TimeRangeFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        :type="'end'"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </TimeRangeFieldInput>
      <TimeRangeFieldInput
        v-else
        :part="segmento.part"
        :type="'end'"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </TimeRangeFieldInput>
    </template>
    <template v-if="name">
      <input
        type="hidden"
        :name="`${name}_inicio`"
        :value="periodo.inicio"
      >
      <input
        type="hidden"
        :name="`${name}_fim`"
        :value="periodo.fim"
      >
    </template>
  </TimeRangeFieldRoot>
</template>

<script setup>
// Intervalo de horas (docs/specs/v8/componentes.md), sobre o TimeRangeField do Reka UI, no
// relógio de 24 horas. O v-model é `{ inicio, fim }` em HH:MM.
//
//   <CampoIntervaloHoras v-model="expediente" name="expediente" rotulo="Expediente" />

// 1. Imports
import { computed } from 'vue'
import { TimeRangeFieldInput, TimeRangeFieldRoot } from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, hora, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'

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
const periodo = defineModel({ type: Object, default: () => ({ inicio: '', fim: '' }) })

// 5. Computed Properties
// O v-model é `{ inicio, fim }` em texto ISO; o Reka trabalha com `{ start, end }` (datas.js).
const valor = computed({
  get: () => periodoParaObjeto(periodo.value, FORMATO),
  set: intervalo => {
    periodo.value = periodoParaTexto(intervalo, FORMATO)
  }
})
</script>
