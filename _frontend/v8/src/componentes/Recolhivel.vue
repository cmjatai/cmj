<template>
  <CollapsibleRoot
    v-model:open="aberto"
    class="v8-recolhivel"
    :disabled="disabled"
  >
    <CollapsibleTrigger class="v8-btn v8-btn-fantasma v8-recolhivel-gatilho">
      <span>{{ titulo }}</span>
      <svg
        class="v8-icone v8-recolhivel-seta"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path :d="ICONES.abaixo" />
      </svg>
    </CollapsibleTrigger>
    <CollapsibleContent class="v8-recolhivel-painel">
      <div class="v8-recolhivel-miolo">
        <slot />
      </div>
    </CollapsibleContent>
  </CollapsibleRoot>
</template>

<script setup>
// Recolhível (docs/specs/v8/componentes.md): um trecho que abre e fecha pelo botão do título,
// sobre o Collapsible do Reka UI. Para várias seções, use `Sanfona`.
//
//   <Recolhivel v-model:open="aberto" titulo="Mais filtros">...</Recolhivel>

// 1. Imports
import { CollapsibleContent, CollapsibleRoot, CollapsibleTrigger } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  titulo: {
    type: String,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const aberto = defineModel('open', { type: Boolean, default: false })
</script>
