<template>
  <TooltipProvider :delay-duration="atraso">
    <TooltipRoot>
      <TooltipTrigger as-child>
        <slot />
      </TooltipTrigger>
      <TooltipPortal>
        <TooltipContent
          class="v8-dica"
          :side="lado"
          :side-offset="6"
        >
          {{ texto }}
          <TooltipArrow
            class="v8-dica-seta"
            :width="10"
            :height="5"
          />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<script setup>
// Dica (docs/specs/v8/componentes.md): texto curto ao passar o mouse ou focar o elemento do slot,
// sobre o Tooltip do Reka UI. O slot é o próprio gatilho, que precisa receber foco.
//
//   <Dica texto="Excluir o registro"><button class="v8-btn v8-btn-icone">...</button></Dica>

// 1. Imports
import { TooltipArrow, TooltipContent, TooltipPortal, TooltipProvider, TooltipRoot, TooltipTrigger } from 'reka-ui'

// 3. Props & Emits
defineProps({
  texto: {
    type: String,
    required: true
  },
  lado: {
    type: String,
    default: 'top'
  },
  // Espera antes de abrir, em milissegundos.
  atraso: {
    type: Number,
    default: 300
  }
})
</script>
