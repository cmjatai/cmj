<template>
  <TagGroupRoot
    v-model="selecionadas"
    class="v8-grupo-etiquetas"
    :selection-mode="selecao"
    :disabled="disabled"
    :aria-label="rotulo || undefined"
    v-bind="removivel ? { onRemove: aoRemover } : {}"
  >
    <TagGroupItem
      v-for="item in itens"
      :key="item.valor"
      class="v8-etiqueta v8-grupo-etiquetas-item"
      :value="item.valor"
      :text-value="item.rotulo"
      :disabled="item.desabilitado"
    >
      <TagGroupItemText>{{ item.rotulo }}</TagGroupItemText>
      <TagGroupItemDelete
        v-if="removivel"
        class="v8-campo-etiquetas-remover"
        :aria-label="`Remover ${item.rotulo}`"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          aria-hidden="true"
        >
          <path :d="ICONES.fechar" />
        </svg>
      </TagGroupItemDelete>
    </TagGroupItem>
  </TagGroupRoot>
</template>

<script setup>
// Grupo de etiquetas (docs/specs/v8/componentes.md), sobre o TagGroup do Reka UI: etiquetas já
// existentes, que podem ser selecionadas (`selecao`) e removidas (`removivel`). Remover só avisa
// pelo evento `remover`, com os valores: quem usa o componente tira o item da lista.
//
//   <GrupoEtiquetas :itens="filtros" removivel @remover="tirarFiltros" />

// 1. Imports
import { TagGroupItem, TagGroupItemDelete, TagGroupItemText, TagGroupRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  // `none`, `single` ou `multiple`.
  selecao: {
    type: String,
    default: 'none'
  },
  removivel: {
    type: Boolean,
    default: false
  },
  rotulo: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const emit = defineEmits(['remover'])
const selecionadas = defineModel({ type: [String, Array], default: undefined })

// 8. Functions
function aoRemover(valores) {
  emit('remover', valores)
}
</script>
