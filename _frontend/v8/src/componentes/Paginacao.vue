<template>
  <PaginationRoot
    v-model:page="pagina"
    class="v8-paginacao"
    :total="total"
    :items-per-page="porPagina"
    :sibling-count="vizinhas"
    show-edges
    :aria-label="rotulo"
  >
    <PaginationList
      v-slot="{ items }"
      class="v8-paginacao-lista"
    >
      <PaginationPrev
        class="v8-btn"
        aria-label="Página anterior"
      >
        Anterior
      </PaginationPrev>
      <template
        v-for="(item, posicao) in items"
        :key="item.type === 'page' ? item.value : `reticencias-${posicao}`"
      >
        <PaginationListItem
          v-if="item.type === 'page'"
          class="v8-btn v8-paginacao-pagina"
          :value="item.value"
          :aria-label="`Página ${item.value}`"
        >
          {{ item.value }}
        </PaginationListItem>
        <PaginationEllipsis
          v-else
          class="v8-paginacao-reticencias"
        >
          …
        </PaginationEllipsis>
      </template>
      <PaginationNext
        class="v8-btn"
        aria-label="Próxima página"
      >
        Próxima
      </PaginationNext>
    </PaginationList>
  </PaginationRoot>
</template>

<script setup>
// Paginação (docs/specs/v8/componentes.md), sobre o Pagination do Reka UI, com o visual de
// `v8-paginacao`. O v-model:page é a página atual, a partir de 1. Nas páginas Django sem
// JavaScript, continue com os links de `v8-paginacao`.
//
//   <Paginacao v-model:page="pagina" :total="resultado.total" :por-pagina="20" />

// 1. Imports
import {
  PaginationEllipsis,
  PaginationList,
  PaginationListItem,
  PaginationNext,
  PaginationPrev,
  PaginationRoot
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  total: {
    type: Number,
    required: true
  },
  porPagina: {
    type: Number,
    default: 10
  },
  // Páginas mostradas de cada lado da atual.
  vizinhas: {
    type: Number,
    default: 1
  },
  rotulo: {
    type: String,
    default: 'Paginação'
  }
})
const pagina = defineModel('page', { type: Number, default: 1 })
</script>
