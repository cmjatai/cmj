<template>
  <DropdownMenuRoot v-model:open="aberto">
    <DropdownMenuTrigger as-child>
      <slot name="gatilho">
        <button
          type="button"
          class="v8-btn"
        >
          {{ rotulo }}
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
        </button>
      </slot>
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent
        class="v8-suspenso"
        :align="alinhamento"
        :side-offset="4"
      >
        <template
          v-for="(item, posicao) in itens"
          :key="item.valor ?? `${posicao}`"
        >
          <DropdownMenuSeparator
            v-if="item.separador"
            class="v8-suspenso-separador"
          />
          <DropdownMenuLabel
            v-else-if="item.titulo"
            class="v8-suspenso-titulo"
          >
            {{ item.titulo }}
          </DropdownMenuLabel>
          <DropdownMenuItem
            v-else
            class="v8-suspenso-item"
            :class="{ 'v8-suspenso-item-perigo': item.perigo }"
            :disabled="item.desabilitado"
            @select="emit('selecionar', item.valor)"
          >
            {{ item.rotulo }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<script setup>
// Menu suspenso (docs/specs/v8/componentes.md): lista de ações aberta por um botão, sobre o
// DropdownMenu do Reka UI. Cada item é `{ valor, rotulo, desabilitado, perigo }`; `{ titulo }`
// é um rótulo de grupo e `{ separador: true }`, uma linha.
//
//   <MenuSuspenso rotulo="Ações" :itens="itens" @selecionar="executar" />

// 1. Imports
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  rotulo: {
    type: String,
    default: 'Ações'
  },
  alinhamento: {
    type: String,
    default: 'start'
  }
})
const emit = defineEmits(['selecionar'])
const aberto = defineModel('open', { type: Boolean, default: false })
</script>
