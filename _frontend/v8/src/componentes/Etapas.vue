<template>
  <StepperRoot
    v-slot="{ totalSteps }"
    v-model="etapa"
    class="v8-etapas"
    :linear="linear"
    :orientation="orientacao"
    :aria-label="rotulo"
  >
    <StepperItem
      v-for="(passo, posicao) in passos"
      :key="posicao"
      class="v8-etapas-item"
      :step="posicao + 1"
      :disabled="passo.desabilitado"
    >
      <StepperTrigger class="v8-etapas-gatilho">
        <StepperIndicator class="v8-etapas-indicador">
          {{ posicao + 1 }}
        </StepperIndicator>
        <span class="v8-etapas-textos">
          <StepperTitle class="v8-etapas-titulo">{{ passo.titulo }}</StepperTitle>
          <StepperDescription
            v-if="passo.descricao"
            class="v8-etapas-descricao"
          >{{ passo.descricao }}</StepperDescription>
        </span>
      </StepperTrigger>
      <StepperSeparator
        v-if="posicao < passos.length - 1"
        class="v8-etapas-separador"
      />
    </StepperItem>
    <p
      class="sr-only"
      role="status"
      aria-live="polite"
      aria-atomic="true"
      data-etapas-aviso
    >
      Etapa {{ etapa }} de {{ totalSteps }}
    </p>
  </StepperRoot>
</template>

<script setup>
// Etapas (docs/specs/v8/componentes.md), sobre o Stepper do Reka UI: os passos de um processo,
// com o atual marcado. O v-model é o passo, a partir de 1. Com `linear`, só se avança um passo
// por vez. Cada passo é `{ titulo, descricao, desabilitado }`. O aviso de passo do Reka sai em
// inglês e fica escondido no CSS; o componente dá o próprio, em português (V8-CMP-008).
//
//   <Etapas v-model="passo" :passos="[{ titulo: 'Protocolo' }, { titulo: 'Comissão' }]" />

// 1. Imports
import {
  StepperDescription,
  StepperIndicator,
  StepperItem,
  StepperRoot,
  StepperSeparator,
  StepperTitle,
  StepperTrigger
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  passos: {
    type: Array,
    required: true
  },
  linear: {
    type: Boolean,
    default: true
  },
  orientacao: {
    type: String,
    default: 'horizontal'
  },
  rotulo: {
    type: String,
    default: 'Etapas'
  }
})
const etapa = defineModel({ type: Number, default: 1 })
</script>
