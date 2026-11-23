<template>
  <MonthRangePickerRoot
    v-slot="{ grid }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || undefined"
    :disabled="disabled"
  >
    <MonthRangePickerHeader class="v8-calendario-cabecalho">
      <MonthRangePickerPrev
        class="v8-btn v8-btn-fantasma v8-btn-icone"
        aria-label="Ano anterior"
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
      </MonthRangePickerPrev>
      <MonthRangePickerHeading class="v8-calendario-titulo" />
      <MonthRangePickerNext
        class="v8-btn v8-btn-fantasma v8-btn-icone"
        aria-label="Próximo ano"
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
      </MonthRangePickerNext>
    </MonthRangePickerHeader>
    <MonthRangePickerGrid class="v8-calendario-grade">
      <MonthRangePickerGridBody>
        <MonthRangePickerGridRow
          v-for="(linha, posicao) in grid.rows"
          :key="`linha-${posicao}`"
        >
          <MonthRangePickerCell
            v-for="data in linha"
            :key="data.toString()"
            :date="data"
            class="v8-calendario-celula"
          >
            <MonthRangePickerCellTrigger
              :month="data"
              class="v8-calendario-dia v8-calendario-mes"
            />
          </MonthRangePickerCell>
        </MonthRangePickerGridRow>
      </MonthRangePickerGridBody>
    </MonthRangePickerGrid>
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
  </MonthRangePickerRoot>
</template>

<script setup>
// Intervalo de meses (docs/specs/v8/componentes.md), sobre o MonthRangePicker do Reka UI, em
// pt-BR. O v-model é `{ inicio, fim }` em AAAA-MM.
//
//   <SeletorMeses v-model="trimestre" name="trimestre" rotulo="Meses" />

// 1. Imports
import { computed } from 'vue'
import {
  MonthRangePickerCell,
  MonthRangePickerCellTrigger,
  MonthRangePickerGrid,
  MonthRangePickerGridBody,
  MonthRangePickerGridRow,
  MonthRangePickerHeader,
  MonthRangePickerHeading,
  MonthRangePickerNext,
  MonthRangePickerPrev,
  MonthRangePickerRoot
} from 'reka-ui'
import { IDIOMA, mes, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'
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
const FORMATO = mes
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
