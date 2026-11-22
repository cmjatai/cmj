<template>
  <SelectRoot
    v-model="valor"
    :name="name || undefined"
    :disabled="disabled"
    :required="required"
  >
    <SelectTrigger
      :id="id || undefined"
      class="v8-entrada v8-selecao-gatilho"
      :aria-label="rotulo || undefined"
      :aria-invalid="invalido || undefined"
    >
      <SelectValue :placeholder="placeholder" />
      <SelectIcon class="v8-selecao-icone">
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
          <path d="M6 9l6 6 6-6" />
        </svg>
      </SelectIcon>
    </SelectTrigger>
    <SelectPortal>
      <SelectContent
        class="v8-selecao"
        position="popper"
        :side-offset="4"
      >
        <SelectViewport class="v8-selecao-lista">
          <SelectItem
            v-for="opcao in opcoes"
            :key="opcao.valor"
            class="v8-selecao-item"
            :value="opcao.valor"
            :disabled="opcao.desabilitado"
          >
            <SelectItemText>{{ opcao.rotulo }}</SelectItemText>
            <SelectItemIndicator class="v8-selecao-marca">
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
                <path d="M5 12l5 5 9-10" />
              </svg>
            </SelectItemIndicator>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>

<script setup>
// Seleção (docs/specs/v8/componentes.md): escolha de um valor numa lista, sobre o Select do Reka
// UI. O gatilho tem o visual de `v8-entrada`. Com `name`, dentro de um <form>, o valor vai no
// envio nativo. Cada opção é `{ valor, rotulo, desabilitado }`, e `valor` não pode ser vazio.
//
//   <Selecao v-model="bairro" name="bairro" :opcoes="opcoes" placeholder="Escolha o bairro" />

// 1. Imports
import {
  SelectContent,
  SelectIcon,
  SelectItem,
  SelectItemIndicator,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  opcoes: {
    type: Array,
    required: true
  },
  placeholder: {
    type: String,
    default: 'Escolha'
  },
  name: {
    type: String,
    default: ''
  },
  id: {
    type: String,
    default: ''
  },
  // Nome acessível, quando não há <label for> apontando para o `id`.
  rotulo: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  invalido: {
    type: Boolean,
    default: false
  }
})
const valor = defineModel({ type: String, default: undefined })
</script>
