<template>
  <AutocompleteRoot
    v-model="texto"
    class="v8-autocompletar"
    :name="name || undefined"
    :disabled="disabled"
  >
    <AutocompleteAnchor class="v8-entrada v8-selecao-busca-ancora">
      <AutocompleteInput
        :id="id || undefined"
        class="v8-selecao-busca-entrada"
        :placeholder="placeholder"
        :aria-label="rotulo || undefined"
      />
    </AutocompleteAnchor>
    <AutocompletePortal>
      <AutocompleteContent
        class="v8-selecao"
        position="popper"
        :side-offset="4"
        hide-when-empty
      >
        <AutocompleteViewport class="v8-selecao-lista">
          <AutocompleteItem
            v-for="sugestao in sugestoes"
            :key="sugestao"
            class="v8-selecao-item"
            :value="sugestao"
          >
            {{ sugestao }}
          </AutocompleteItem>
        </AutocompleteViewport>
      </AutocompleteContent>
    </AutocompletePortal>
  </AutocompleteRoot>
</template>

<script setup>
// Campo com sugestões (docs/specs/v8/componentes.md), sobre o Autocomplete do Reka UI: o v-model
// é o texto digitado, livre, e as sugestões que contêm esse texto aparecem abaixo para completar.
//
//   <Autocompletar v-model="cidade" name="cidade" rotulo="Cidade" :sugestoes="cidades" />

// 1. Imports
import {
  AutocompleteAnchor,
  AutocompleteContent,
  AutocompleteInput,
  AutocompleteItem,
  AutocompletePortal,
  AutocompleteRoot,
  AutocompleteViewport
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  sugestoes: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: ''
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
