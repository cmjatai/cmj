<template>
  <EditableRoot
    :id="id || undefined"
    v-slot="{ isEditing }"
    v-model="texto"
    class="v8-texto-editavel"
    :placeholder="placeholder"
    :name="name || undefined"
    :disabled="disabled"
    submit-mode="both"
    activation-mode="dblclick"
  >
    <EditableArea class="v8-texto-editavel-area">
      <EditablePreview class="v8-texto-editavel-leitura" />
      <EditableInput
        class="v8-entrada"
        :aria-label="rotulo || 'Texto'"
      />
    </EditableArea>
    <div class="v8-texto-editavel-acoes">
      <EditableEditTrigger
        v-if="!isEditing"
        class="v8-btn v8-btn-fantasma v8-btn-icone"
        aria-label="Editar"
      >
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
          <path :d="ICONES.editar" />
        </svg>
      </EditableEditTrigger>
      <template v-else>
        <EditableSubmitTrigger class="v8-btn v8-btn-primario">
          Salvar
        </EditableSubmitTrigger>
        <EditableCancelTrigger class="v8-btn v8-btn-fantasma">
          Cancelar
        </EditableCancelTrigger>
      </template>
    </div>
  </EditableRoot>
</template>

<script setup>
// Texto editável no lugar (docs/specs/v8/componentes.md), sobre o Editable do Reka UI: mostra o
// texto e o troca por um campo com duplo clique ou pelo botão de editar. Enter ou sair do campo
// salva; ESC cancela.
//
//   <TextoEditavel v-model="titulo" name="titulo" rotulo="Título" />

// 1. Imports
import {
  EditableArea,
  EditableCancelTrigger,
  EditableEditTrigger,
  EditableInput,
  EditablePreview,
  EditableRoot,
  EditableSubmitTrigger
} from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  placeholder: {
    type: String,
    default: 'Sem texto'
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
const texto = defineModel({ type: String, default: '' })
</script>
