<template>
  <DatePickerRoot
    :id="id || undefined"
    v-model="valor"
    v-model:open="aberto"
    :locale="IDIOMA"
    :disabled="disabled"
    fixed-weeks
    close-on-select
  >
    <DatePickerField
      v-slot="{ segments }"
      class="v8-entrada v8-campo-data"
      :aria-label="rotulo || undefined"
    >
      <template
        v-for="segmento in segments"
        :key="segmento.part"
      >
        <DatePickerInput
          v-if="segmento.part === 'literal'"
          :part="segmento.part"
          class="v8-campo-data-literal"
        >
          {{ segmento.value }}
        </DatePickerInput>
        <DatePickerInput
          v-else
          :part="segmento.part"
          :aria-label="NOMES_DAS_PARTES[segmento.part]"
          class="v8-campo-data-segmento"
        >
          {{ segmento.value }}
        </DatePickerInput>
      </template>
      <DatePickerTrigger
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
      </DatePickerTrigger>
      <input
        v-if="name"
        type="hidden"
        :name="name"
        :value="texto"
      >
    </DatePickerField>
    <DatePickerContent
      class="v8-popover v8-seletor-data"
      :side-offset="6"
      align="start"
    >
      <DatePickerCalendar
        v-slot="{ grid, weekDays }"
        class="v8-calendario"
      >
        <DatePickerHeader class="v8-calendario-cabecalho">
          <DatePickerPrev
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
          </DatePickerPrev>
          <DatePickerHeading class="v8-calendario-titulo" />
          <DatePickerNext
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
          </DatePickerNext>
        </DatePickerHeader>
        <DatePickerGrid
          v-for="mes in grid"
          :key="mes.value.toString()"
          class="v8-calendario-grade"
        >
          <DatePickerGridHead>
            <DatePickerGridRow>
              <DatePickerHeadCell
                v-for="diaDaSemana in weekDays"
                :key="diaDaSemana"
                class="v8-calendario-dia-semana"
              >
                {{ diaDaSemana }}
              </DatePickerHeadCell>
            </DatePickerGridRow>
          </DatePickerGridHead>
          <DatePickerGridBody>
            <DatePickerGridRow
              v-for="(semana, posicao) in mes.rows"
              :key="`semana-${posicao}`"
            >
              <DatePickerCell
                v-for="data in semana"
                :key="data.toString()"
                :date="data"
                class="v8-calendario-celula"
              >
                <DatePickerCellTrigger
                  :day="data"
                  :month="mes.value"
                  class="v8-calendario-dia"
                />
              </DatePickerCell>
            </DatePickerGridRow>
          </DatePickerGridBody>
        </DatePickerGrid>
      </DatePickerCalendar>
    </DatePickerContent>
  </DatePickerRoot>
</template>

<script setup>
// Seletor de data (docs/specs/v8/componentes.md), sobre o DatePicker do Reka UI: a data é digitada
// por partes ou escolhida no calendário que abre pelo botão, em pt-BR. O v-model é AAAA-MM-DD.
//
//   <SeletorData v-model="data" name="data" rotulo="Data da sessão" />

// 1. Imports
import { computed } from 'vue'
import {
  DatePickerCalendar,
  DatePickerCell,
  DatePickerCellTrigger,
  DatePickerContent,
  DatePickerField,
  DatePickerGrid,
  DatePickerGridBody,
  DatePickerGridHead,
  DatePickerGridRow,
  DatePickerHeadCell,
  DatePickerHeader,
  DatePickerHeading,
  DatePickerInput,
  DatePickerNext,
  DatePickerPrev,
  DatePickerRoot,
  DatePickerTrigger
} from 'reka-ui'
import { IDIOMA, NOMES_DAS_PARTES, dia } from '~@/componentes/datas'
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
