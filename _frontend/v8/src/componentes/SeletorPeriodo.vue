<template>
  <DateRangePickerRoot
    :id="id || undefined"
    v-model="valor"
    v-model:open="aberto"
    :locale="IDIOMA"
    :disabled="disabled"
    fixed-weeks
    close-on-select
  >
    <DateRangePickerField
      v-slot="{ segments }"
      class="v8-entrada v8-campo-data"
      :aria-label="rotulo || undefined"
    >
      <template
        v-for="segmento in segments.start"
        :key="segmento.part"
      >
        <DateRangePickerInput
          v-if="segmento.part === 'literal'"
          :part="segmento.part"
          :type="'start'"
          class="v8-campo-data-literal"
        >
          {{ segmento.value }}
        </DateRangePickerInput>
        <DateRangePickerInput
          v-else
          :part="segmento.part"
          :type="'start'"
          :aria-label="NOMES_DAS_PARTES[segmento.part]"
          class="v8-campo-data-segmento"
        >
          {{ segmento.value }}
        </DateRangePickerInput>
      </template>
      <span
        class="v8-campo-data-literal"
        aria-hidden="true"
      >–</span>
      <template
        v-for="segmento in segments.end"
        :key="segmento.part"
      >
        <DateRangePickerInput
          v-if="segmento.part === 'literal'"
          :part="segmento.part"
          :type="'end'"
          class="v8-campo-data-literal"
        >
          {{ segmento.value }}
        </DateRangePickerInput>
        <DateRangePickerInput
          v-else
          :part="segmento.part"
          :type="'end'"
          :aria-label="NOMES_DAS_PARTES[segmento.part]"
          class="v8-campo-data-segmento"
        >
          {{ segmento.value }}
        </DateRangePickerInput>
      </template>
      <DateRangePickerTrigger
        class="v8-btn v8-btn-fantasma v8-btn-icone v8-campo-data-gatilho"
        aria-label="Abrir calendário"
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
          <path :d="ICONES.calendario" />
        </svg>
      </DateRangePickerTrigger>
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
    </DateRangePickerField>
    <DateRangePickerContent
      class="v8-popover v8-seletor-data"
      :side-offset="6"
      align="start"
    >
      <DateRangePickerCalendar
        v-slot="{ grid, weekDays }"
        class="v8-calendario"
      >
        <DateRangePickerHeader class="v8-calendario-cabecalho">
          <DateRangePickerPrev
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
          </DateRangePickerPrev>
          <DateRangePickerHeading class="v8-calendario-titulo" />
          <DateRangePickerNext
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
          </DateRangePickerNext>
        </DateRangePickerHeader>
        <DateRangePickerGrid
          v-for="mes in grid"
          :key="mes.value.toString()"
          class="v8-calendario-grade"
        >
          <DateRangePickerGridHead>
            <DateRangePickerGridRow>
              <DateRangePickerHeadCell
                v-for="diaDaSemana in weekDays"
                :key="diaDaSemana"
                class="v8-calendario-dia-semana"
              >
                {{ diaDaSemana }}
              </DateRangePickerHeadCell>
            </DateRangePickerGridRow>
          </DateRangePickerGridHead>
          <DateRangePickerGridBody>
            <DateRangePickerGridRow
              v-for="(semana, posicao) in mes.rows"
              :key="`semana-${posicao}`"
            >
              <DateRangePickerCell
                v-for="data in semana"
                :key="data.toString()"
                :date="data"
                class="v8-calendario-celula"
              >
                <DateRangePickerCellTrigger
                  :day="data"
                  :month="mes.value"
                  class="v8-calendario-dia"
                />
              </DateRangePickerCell>
            </DateRangePickerGridRow>
          </DateRangePickerGridBody>
        </DateRangePickerGrid>
      </DateRangePickerCalendar>
    </DateRangePickerContent>
  </DateRangePickerRoot>
</template>

<script setup>
// Seletor de período (docs/specs/v8/componentes.md), sobre o DateRangePicker do Reka UI: início e
// fim digitados por partes ou escolhidos no calendário, em pt-BR. O v-model é `{ inicio, fim }`
// em AAAA-MM-DD. Com `name`, vai no formulário em `<name>_inicio` e `<name>_fim`.
//
//   <SeletorPeriodo v-model="periodo" name="periodo" rotulo="Período" />

// 1. Imports
import { computed } from 'vue'
import {
  DateRangePickerCalendar,
  DateRangePickerCell,
  DateRangePickerCellTrigger,
  DateRangePickerContent,
  DateRangePickerField,
  DateRangePickerGrid,
  DateRangePickerGridBody,
  DateRangePickerGridHead,
  DateRangePickerGridRow,
  DateRangePickerHeadCell,
  DateRangePickerHeader,
  DateRangePickerHeading,
  DateRangePickerInput,
  DateRangePickerNext,
  DateRangePickerPrev,
  DateRangePickerRoot,
  DateRangePickerTrigger
} from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, dia, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'
import { ICONES } from '~@/componentes/icones'

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
const aberto = defineModel('open', { type: Boolean, default: false })
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
