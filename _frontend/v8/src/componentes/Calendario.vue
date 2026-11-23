<template>
  <CalendarRoot
    v-slot="{ grid, weekDays }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || 'Calendário'"
    :disabled="disabled"
    fixed-weeks
  >
    <CalendarHeader class="v8-calendario-cabecalho">
      <CalendarPrev
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
      </CalendarPrev>
      <CalendarHeading class="v8-calendario-titulo" />
      <CalendarNext
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
      </CalendarNext>
    </CalendarHeader>
    <CalendarGrid
      v-for="mes in grid"
      :key="mes.value.toString()"
      class="v8-calendario-grade"
    >
      <CalendarGridHead>
        <CalendarGridRow>
          <CalendarHeadCell
            v-for="diaDaSemana in weekDays"
            :key="diaDaSemana"
            class="v8-calendario-dia-semana"
          >
            {{ diaDaSemana }}
          </CalendarHeadCell>
        </CalendarGridRow>
      </CalendarGridHead>
      <CalendarGridBody>
        <CalendarGridRow
          v-for="(semana, posicao) in mes.rows"
          :key="`semana-${posicao}`"
        >
          <CalendarCell
            v-for="data in semana"
            :key="data.toString()"
            :date="data"
            class="v8-calendario-celula"
          >
            <CalendarCellTrigger
              :day="data"
              :month="mes.value"
              class="v8-calendario-dia"
            />
          </CalendarCell>
        </CalendarGridRow>
      </CalendarGridBody>
    </CalendarGrid>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="texto"
    >
  </CalendarRoot>
</template>

<script setup>
// Calendário (docs/specs/v8/componentes.md), sobre o Calendar do Reka UI, em pt-BR. O v-model é o
// dia escolhido, em texto AAAA-MM-DD; clicar de novo no dia desmarca. Com `name`, o dia vai no
// formulário num campo oculto.
//
//   <Calendario v-model="data" name="data" rotulo="Data da sessão" />

// 1. Imports
import { computed } from 'vue'
import {
  CalendarCell,
  CalendarCellTrigger,
  CalendarGrid,
  CalendarGridBody,
  CalendarGridHead,
  CalendarGridRow,
  CalendarHeadCell,
  CalendarHeader,
  CalendarHeading,
  CalendarNext,
  CalendarPrev,
  CalendarRoot
} from 'reka-ui'
import { IDIOMA, dia } from '~@/componentes/datas'
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
