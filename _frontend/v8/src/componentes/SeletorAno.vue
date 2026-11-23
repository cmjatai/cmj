<template>
  <YearPickerRoot
    v-slot="{ grid }"
    v-model="valor"
    class="v8-calendario"
    :locale="IDIOMA"
    :calendar-label="rotulo || undefined"
    :disabled="disabled"
  >
    <YearPickerHeader class="v8-calendario-cabecalho">
      <YearPickerPrev
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
      </YearPickerPrev>
      <YearPickerHeading class="v8-calendario-titulo" />
      <YearPickerNext
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
      </YearPickerNext>
    </YearPickerHeader>
    <YearPickerGrid class="v8-calendario-grade">
      <YearPickerGridBody>
        <YearPickerGridRow
          v-for="(linha, posicao) in grid.rows"
          :key="`linha-${posicao}`"
        >
          <YearPickerCell
            v-for="data in linha"
            :key="data.toString()"
            :date="data"
            class="v8-calendario-celula"
          >
            <YearPickerCellTrigger
              :year="data"
              class="v8-calendario-dia v8-calendario-mes"
            />
          </YearPickerCell>
        </YearPickerGridRow>
      </YearPickerGridBody>
    </YearPickerGrid>
    <input
      v-if="name"
      type="hidden"
      :name="name"
      :value="texto"
    >
  </YearPickerRoot>
</template>

<script setup>
// Seletor de ano (docs/specs/v8/componentes.md), sobre o YearPicker do Reka UI. O v-model é AAAA,
// sem mês nem dia (V8-CMP-031).
//
//   <SeletorAno v-model="exercicio" name="exercicio" rotulo="Exercício" />

// 1. Imports
import { computed } from 'vue'
import {
  YearPickerCell,
  YearPickerCellTrigger,
  YearPickerGrid,
  YearPickerGridBody,
  YearPickerGridRow,
  YearPickerHeader,
  YearPickerHeading,
  YearPickerNext,
  YearPickerPrev,
  YearPickerRoot
} from 'reka-ui'
import { IDIOMA, ano } from '~@/componentes/datas'
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
