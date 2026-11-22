<template>
  <TagsInputRoot
    :id="id || undefined"
    v-model="etiquetas"
    class="v8-entrada v8-campo-etiquetas"
    :max="max"
    :name="name || undefined"
    :disabled="disabled"
    add-on-blur
    add-on-paste
  >
    <TagsInputItem
      v-for="etiqueta in etiquetas"
      :key="etiqueta"
      class="v8-etiqueta v8-campo-etiquetas-item"
      :value="etiqueta"
    >
      <TagsInputItemText />
      <TagsInputItemDelete
        class="v8-campo-etiquetas-remover"
        :aria-label="`Remover ${etiqueta}`"
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
      </TagsInputItemDelete>
    </TagsInputItem>
    <TagsInputInput
      class="v8-campo-etiquetas-entrada"
      :placeholder="placeholder"
      :aria-label="rotulo || undefined"
    />
  </TagsInputRoot>
</template>

<script setup>
// Campo de etiquetas (docs/specs/v8/componentes.md), sobre o TagsInput do Reka UI: o texto
// digitado vira etiqueta com Enter, vírgula ou ao sair do campo. O v-model é a lista de textos.
//
//   <CampoEtiquetas v-model="assuntos" name="assuntos" placeholder="Novo assunto" />

// 1. Imports
import { TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText, TagsInputRoot } from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  placeholder: {
    type: String,
    default: ''
  },
  // Quantidade máxima de etiquetas; 0 é sem limite.
  max: {
    type: Number,
    default: 0
  },
  rotulo: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: ''
  },
  id: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
const etiquetas = defineModel({ type: Array, default: () => [] })
</script>
