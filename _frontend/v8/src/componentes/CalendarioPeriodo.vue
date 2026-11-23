<template>
  <RangeCalendarRoot
    v-slot="{ grid, weekDays }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || 'Calendário de período'"
    :disabled="disabled"
    :number-of-months="meses"
    fixed-weeks
  >
    <div class="v8-calendario-meses">
      <RangeCalendarHeader class="v8-calendario-cabecalho">
        <RangeCalendarPrev
          class="v8-btn v8-btn-fantasma v8-btn-icone"
          aria-label="Mês anterior"
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
        </RangeCalendarPrev>
        <RangeCalendarHeading class="v8-calendario-titulo" />
        <RangeCalendarNext
          class="v8-btn v8-btn-fantasma v8-btn-icone"
          aria-label="Próximo mês"
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
        </RangeCalendarNext>
      </RangeCalendarHeader>
      <RangeCalendarGrid
        v-for="mes in grid"
        :key="mes.value.toString()"
        class="v8-calendario-grade"
      >
        <RangeCalendarGridHead>
          <RangeCalendarGridRow>
            <RangeCalendarHeadCell
              v-for="diaDaSemana in weekDays"
              :key="diaDaSemana"
              class="v8-calendario-dia-semana"
            >
              {{ diaDaSemana }}
            </RangeCalendarHeadCell>
          </RangeCalendarGridRow>
        </RangeCalendarGridHead>
        <RangeCalendarGridBody>
          <RangeCalendarGridRow
            v-for="(semana, posicao) in mes.rows"
            :key="`semana-${posicao}`"
          >
            <RangeCalendarCell
              v-for="data in semana"
              :key="data.toString()"
              :date="data"
              class="v8-calendario-celula"
            >
              <RangeCalendarCellTrigger
                :day="data"
                :month="mes.value"
                class="v8-calendario-dia"
              />
            </RangeCalendarCell>
          </RangeCalendarGridRow>
        </RangeCalendarGridBody>
      </RangeCalendarGrid>
    </div>
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
  </RangeCalendarRoot>
</template>

<script setup>
// Calendário de período (docs/specs/v8/componentes.md), sobre o RangeCalendar do Reka UI, em
// pt-BR: o primeiro clique marca o início e o segundo, o fim. O v-model é `{ inicio, fim }` em
// AAAA-MM-DD. Com `name`, vai no formulário em `<name>_inicio` e `<name>_fim`.
//
//   <CalendarioPeriodo v-model="periodo" name="periodo" :meses="2" />

// 1. Imports
import { computed } from 'vue'
import {
  RangeCalendarCell,
  RangeCalendarCellTrigger,
  RangeCalendarGrid,
  RangeCalendarGridBody,
  RangeCalendarGridHead,
  RangeCalendarGridRow,
  RangeCalendarHeadCell,
  RangeCalendarHeader,
  RangeCalendarHeading,
  RangeCalendarNext,
  RangeCalendarPrev,
  RangeCalendarRoot
} from 'reka-ui'
import { IDIOMA, dia, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  // Quantos meses aparecem lado a lado.
  meses: {
    type: Number,
    default: 1
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
