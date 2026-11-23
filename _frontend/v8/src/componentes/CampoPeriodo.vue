<template>
  <DateRangeFieldRoot
    :id="id || undefined"
    v-slot="{ segments }"
    v-model="valor"
    class="v8-entrada v8-campo-data"
    :locale="IDIOMA"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
  >
    <template
      v-for="segmento in segments.start"
      :key="segmento.part"
    >
      <DateRangeFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        :type="'start'"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </DateRangeFieldInput>
      <DateRangeFieldInput
        v-else
        :part="segmento.part"
        :type="'start'"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </DateRangeFieldInput>
    </template>
    <span
      class="v8-campo-data-literal"
      aria-hidden="true"
    >–</span>
    <template
      v-for="segmento in segments.end"
      :key="segmento.part"
    >
      <DateRangeFieldInput
        v-if="segmento.part === 'literal'"
        :part="segmento.part"
        :type="'end'"
        class="v8-campo-data-literal"
      >
        {{ segmento.value }}
      </DateRangeFieldInput>
      <DateRangeFieldInput
        v-else
        :part="segmento.part"
        :type="'end'"
        :aria-label="NOMES_DAS_PARTES[segmento.part]"
        class="v8-campo-data-segmento"
      >
        {{ segmento.value }}
      </DateRangeFieldInput>
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
  </DateRangeFieldRoot>
</template>

<script setup>
// Campo de período (docs/specs/v8/componentes.md), sobre o DateRangeField do Reka UI: início e
// fim digitados por partes, em pt-BR. O v-model é `{ inicio, fim }` em AAAA-MM-DD.
//
//   <CampoPeriodo v-model="vigencia" name="vigencia" rotulo="Vigência" />

// 1. Imports
import { computed } from 'vue'
import { DateRangeFieldInput, DateRangeFieldRoot } from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, dia, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'

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
