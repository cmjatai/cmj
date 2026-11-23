<template>
  <MonthPickerRoot
    v-slot="{ grid }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || undefined"
    :disabled="disabled"
  >
    <MonthPickerHeader class="v8-calendario-cabecalho">
      <MonthPickerPrev
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
      </MonthPickerPrev>
      <MonthPickerHeading class="v8-calendario-titulo" />
      <MonthPickerNext
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
      </MonthPickerNext>
    </MonthPickerHeader>
    <MonthPickerGrid class="v8-calendario-grade">
      <MonthPickerGridBody>
        <MonthPickerGridRow
          v-for="(linha, posicao) in grid.rows"
          :key="`linha-${posicao}`"
        >
          <MonthPickerCell
            v-for="data in linha"
            :key="data.toString()"
            :date="data"
            class="v8-calendario-celula"
          >
            <MonthPickerCellTrigger
              :month="data"
              class="v8-calendario-dia v8-calendario-mes"
            />
          </MonthPickerCell>
        </MonthPickerGridRow>
      </MonthPickerGridBody>
    </MonthPickerGrid>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="texto"
    >
  </MonthPickerRoot>
</template>

<script setup>
// Seletor de mês (docs/specs/v8/componentes.md), sobre o MonthPicker do Reka UI, em pt-BR. O
// v-model é AAAA-MM, sem o dia (V8-CMP-031).
//
//   <SeletorMes v-model="competencia" name="competencia" rotulo="Competência" />

// 1. Imports
import { computed } from 'vue'
import {
  MonthPickerCell,
  MonthPickerCellTrigger,
  MonthPickerGrid,
  MonthPickerGridBody,
  MonthPickerGridRow,
  MonthPickerHeader,
  MonthPickerHeading,
  MonthPickerNext,
  MonthPickerPrev,
  MonthPickerRoot
} from 'reka-ui'
import { IDIOMA, mes } from '~@/componentes/datas'
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
