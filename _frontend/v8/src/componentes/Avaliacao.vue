<template>
  <RatingRoot
    v-slot="{ items }"
    v-model="nota"
    class="v8-avaliacao"
    :length="tamanho"
    :name="name || undefined"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
    hoverable
  >
    <RatingItem
      v-for="item in items"
      :key="item"
      v-slot="{ steps }"
      class="v8-avaliacao-item"
      :item="item"
    >
      <RatingItemIndicator
        v-for="passo in steps"
        :key="passo"
        class="v8-avaliacao-estrela"
        :step="passo"
        :aria-label="`${item} de ${tamanho}`"
      >
        <svg
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="ICONES.estrela" />
        </svg>
      </RatingItemIndicator>
    </RatingItem>
  </RatingRoot>
</template>

<script setup>
// Avaliação em estrelas (docs/specs/v8/componentes.md), sobre o Rating do Reka UI. O v-model é a
// nota, de 0 a `tamanho`.
//
//   <Avaliacao v-model="nota" name="nota" rotulo="Nota do atendimento" />

// 1. Imports
import { RatingItem, RatingItemIndicator, RatingRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  tamanho: {
    type: Number,
    default: 5
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
const nota = defineModel({ type: Number, default: 0 })
</script>
