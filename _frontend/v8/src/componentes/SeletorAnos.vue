<template>
  <YearRangePickerRoot
    v-slot="{ grid }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || undefined"
    :disabled="disabled"
  >
    <YearRangePickerHeader class="v8-calendario-cabecalho">
      <YearRangePickerPrev
        class="v8-btn v8-btn-fantasma v8-btn-icone"
        aria-label="Anos anteriores"
      >
        <svg
          class="v8-icone"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="ICONES.esquerda" />
        </svg>
      </YearRangePickerPrev>
      <YearRangePickerHeading class="v8-calendario-titulo" />
      <YearRangePickerNext
        class="v8-btn v8-btn-fantasma v8-btn-icone"
        aria-label="Próximos anos"
      >
        <svg
          class="v8-icone"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="ICONES.direita" />
        </svg>
      </YearRangePickerNext>
    </YearRangePickerHeader>
    <YearRangePickerGrid class="v8-calendario-grade">
      <YearRangePickerGridBody>
        <YearRangePickerGridRow
          v-for="(linha, posicao) in grid.rows"
          :key="`linha-${posicao}`"
        >
          <YearRangePickerCell
            v-for="data in linha"
            :key="data.toString()"
            :date="data"
            class="v8-calendario-celula"
          >
            <YearRangePickerCellTrigger
              :year="data"
              class="v8-calendario-dia v8-calendario-mes"
            />
          </YearRangePickerCell>
        </YearRangePickerGridRow>
      </YearRangePickerGridBody>
    </YearRangePickerGrid>
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
  </YearRangePickerRoot>
</template>

<script setup>
// Intervalo de anos (docs/specs/v8/componentes.md), sobre o YearRangePicker do Reka UI. O v-model
// é `{ inicio, fim }` em AAAA.
//
//   <SeletorAnos v-model="legislatura" name="legislatura" rotulo="Anos" />

// 1. Imports
import { computed } from 'vue'
import {
  YearRangePickerCell,
  YearRangePickerCellTrigger,
  YearRangePickerGrid,
  YearRangePickerGridBody,
  YearRangePickerGridRow,
  YearRangePickerHeader,
  YearRangePickerHeading,
  YearRangePickerNext,
  YearRangePickerPrev,
  YearRangePickerRoot
} from 'reka-ui'
import { IDIOMA, ano, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'
import { ICONES } from '~@/componentes/icones'

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
  disabled: {
    type: Boolean,
    default: false
  }
})
const FORMATO = ano
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
