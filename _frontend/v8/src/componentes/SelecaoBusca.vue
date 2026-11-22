<template>
  <ComboboxRoot
    v-model="valor"
    class="v8-selecao-busca"
    :multiple="multipla"
    :name="name || undefined"
    :disabled="disabled"
    open-on-click
  >
    <ComboboxAnchor class="v8-entrada v8-selecao-busca-ancora">
      <ComboboxInput
        :id="id || undefined"
        class="v8-selecao-busca-entrada"
        :placeholder="placeholder"
        :display-value="rotuloDe"
        :aria-label="rotulo || undefined"
      />
      <ComboboxTrigger
        class="v8-selecao-icone"
        aria-label="Mostrar opções"
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
          <path :d="ICONES.abaixo" />
        </svg>
      </ComboboxTrigger>
    </ComboboxAnchor>
    <ComboboxPortal>
      <ComboboxContent
        class="v8-selecao v8-selecao-busca-lista"
        position="popper"
        :side-offset="4"
      >
        <ComboboxViewport class="v8-selecao-lista">
          <ComboboxEmpty class="v8-selecao-vazia">
            {{ vazio }}
          </ComboboxEmpty>
          <ComboboxItem
            v-for="opcao in opcoes"
            :key="opcao.valor"
            class="v8-selecao-item"
            :value="opcao.valor"
            :text-value="opcao.rotulo"
            :disabled="opcao.desabilitado"
          >
            <span>{{ opcao.rotulo }}</span>
            <ComboboxItemIndicator class="v8-selecao-marca">
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
            </ComboboxItemIndicator>
          </ComboboxItem>
        </ComboboxViewport>
      </ComboboxContent>
    </ComboboxPortal>
  </ComboboxRoot>
</template>

<script setup>
// Seleção com busca (docs/specs/v8/componentes.md), sobre o Combobox do Reka UI: o texto digitado
// filtra as opções, e o v-model é o `valor` escolhido (ou a lista, com `multipla`). Cada opção é
// `{ valor, rotulo, desabilitado }`, e `valor` não pode ser vazio.
//
//   <SelecaoBusca v-model="bairro" name="bairro" rotulo="Bairro" :opcoes="opcoes" />

// 1. Imports
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxItemIndicator,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxTrigger,
  ComboboxViewport
} from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
const props = defineProps({
  opcoes: {
    type: Array,
    required: true
  },
  multipla: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: 'Buscar'
  },
  vazio: {
    type: String,
    default: 'Nada encontrado.'
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
const valor = defineModel({ type: [String, Array], default: undefined })

// 8. Functions
// O campo mostra o rótulo da opção escolhida, não o valor; com várias, a lista de rótulos.
function rotuloDe(escolhido) {
  const lista = Array.isArray(escolhido) ? escolhido : [escolhido]
  return lista
    .map(v => props.opcoes.find(opcao => opcao.valor === v)?.rotulo)
    .filter(Boolean)
    .join(', ')
}
</script>
