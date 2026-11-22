<template>
  <ListboxRoot
    v-model="valor"
    class="v8-lista-opcoes"
    :multiple="multipla"
    :name="name || undefined"
    :disabled="disabled"
  >
    <ListboxContent
      class="v8-lista-opcoes-conteudo"
      :aria-label="rotulo || undefined"
    >
      <ListboxItem
        v-for="opcao in opcoes"
        :key="opcao.valor"
        class="v8-selecao-item"
        :value="opcao.valor"
        :disabled="opcao.desabilitado"
      >
        <span>{{ opcao.rotulo }}</span>
        <ListboxItemIndicator class="v8-selecao-marca">
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
            <path :d="ICONES.marca" />
          </svg>
        </ListboxItemIndicator>
      </ListboxItem>
    </ListboxContent>
  </ListboxRoot>
</template>

<script setup>
// Lista de opções sempre visível (docs/specs/v8/componentes.md), sobre o Listbox do Reka UI, com
// uma escolha ou várias (`multipla`). Cada opção é `{ valor, rotulo, desabilitado }`.
//
//   <ListaOpcoes v-model="temas" name="temas" rotulo="Temas" multipla :opcoes="opcoes" />

// 1. Imports
import { ListboxContent, ListboxItem, ListboxItemIndicator, ListboxRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  opcoes: {
    type: Array,
    required: true
  },
  multipla: {
    type: Boolean,
    default: false
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
const valor = defineModel({ type: [String, Array], default: undefined })
</script>
