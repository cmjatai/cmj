<template>
  <TreeRoot
    v-slot="{ flattenItems }"
    v-model="selecionado"
    v-model:expanded="abertos"
    class="v8-arvore"
    :items="itens"
    :get-key="item => item.valor"
    :get-children="item => item.filhos"
    :aria-label="rotulo || undefined"
  >
    <TreeItem
      v-for="item in flattenItems"
      :key="item._id"
      v-slot="{ isExpanded }"
      v-bind="item.bind"
      class="v8-arvore-item"
      :style="{ paddingInlineStart: `${(item.level - 1) * 1.25 + 0.5}rem` }"
    >
      <svg
        v-if="item.hasChildren"
        class="v8-icone v8-arvore-seta"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path :d="isExpanded ? ICONES.abaixo : ICONES.direita" />
      </svg>
      <span
        v-else
        class="v8-arvore-folha"
      />
      <span>{{ item.value.rotulo }}</span>
    </TreeItem>
  </TreeRoot>
</template>

<script setup>
// Árvore (docs/specs/v8/componentes.md), sobre o Tree do Reka UI: itens hierárquicos que abrem e
// fecham. Cada item é `{ valor, rotulo, filhos }`, com `valor` único na árvore. O v-model é o
// item selecionado, e v-model:expanded, a lista dos `valor` abertos.
//
//   <Arvore v-model="pasta" v-model:expanded="abertas" rotulo="Pastas" :itens="pastas" />

// 1. Imports
import { TreeItem, TreeRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  rotulo: {
    type: String,
    default: ''
  }
})
const selecionado = defineModel({ type: Object, default: undefined })
const abertos = defineModel('expanded', { type: Array, default: () => [] })
</script>
