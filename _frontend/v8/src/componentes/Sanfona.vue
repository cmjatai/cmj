<template>
  <AccordionRoot
    v-model="valor"
    class="v8-sanfona"
    :type="multipla ? 'multiple' : 'single'"
    collapsible
  >
    <AccordionItem
      v-for="item in itens"
      :key="item.valor"
      class="v8-sanfona-item"
      :value="item.valor"
      :disabled="item.desabilitado"
    >
      <AccordionHeader
        class="v8-sanfona-cabecalho"
        :as="nivel"
      >
        <AccordionTrigger class="v8-sanfona-gatilho">
          <span>{{ item.titulo }}</span>
          <svg
            class="v8-sanfona-seta"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </AccordionTrigger>
      </AccordionHeader>
      <AccordionContent class="v8-sanfona-painel">
        <div class="v8-sanfona-miolo">
          <slot
            :name="item.valor"
            :item="item"
          />
        </div>
      </AccordionContent>
    </AccordionItem>
  </AccordionRoot>
</template>

<script setup>
// Sanfona (docs/specs/v8/componentes.md): seções que abrem e fecham, sobre o Accordion do Reka UI.
//
//   <Sanfona v-model="aberta" :itens="[{ valor: 'a', titulo: 'Primeira' }]">
//     <template #a>...</template>
//   </Sanfona>
//
// Com `multipla`, várias seções ficam abertas ao mesmo tempo e o v-model é uma lista.

// 1. Imports
import { AccordionContent, AccordionHeader, AccordionItem, AccordionRoot, AccordionTrigger } from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  multipla: {
    type: Boolean,
    default: false
  },
  // Elemento de título que envolve cada gatilho.
  nivel: {
    type: String,
    default: 'h3'
  }
})
const valor = defineModel({ type: [String, Array], default: undefined })
</script>
