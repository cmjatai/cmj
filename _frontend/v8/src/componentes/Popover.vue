<template>
  <PopoverRoot v-model:open="aberto">
    <PopoverTrigger as-child>
      <slot name="gatilho" />
    </PopoverTrigger>
    <PopoverPortal>
      <PopoverContent
        class="v8-popover"
        :side="lado"
        :align="alinhamento"
        :side-offset="6"
        :aria-label="titulo || undefined"
      >
        <div class="v8-popover-cabecalho">
          <p
            v-if="titulo"
            class="v8-popover-titulo"
          >
            {{ titulo }}
          </p>
          <PopoverClose
            class="v8-btn v8-btn-fantasma v8-btn-icone v8-popover-fechar"
            aria-label="Fechar"
          >
            <svg
              class="v8-icone"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              aria-hidden="true"
            >
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </PopoverClose>
        </div>
        <slot :fechar="fechar" />
        <PopoverArrow
          class="v8-popover-seta"
          :width="12"
          :height="6"
        />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<script setup>
// Popover (docs/specs/v8/componentes.md): painel flutuante ancorado num gatilho, sobre o Popover
// do Reka UI. Fecha com ESC, com o botão de fechar e ao clicar fora.
//
//   <Popover titulo="Filtros">
//     <template #gatilho><button class="v8-btn">Filtros</button></template>
//     <template #default="{ fechar }">...</template>
//   </Popover>

// 1. Imports
import { PopoverArrow, PopoverClose, PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'

// 3. Props & Emits
defineProps({
  titulo: {
    type: String,
    default: ''
  },
  lado: {
    type: String,
    default: 'bottom'
  },
  alinhamento: {
    type: String,
    default: 'center'
  }
})
const aberto = defineModel('open', { type: Boolean, default: false })

// 8. Functions
function fechar() {
  aberto.value = false
}
</script>
