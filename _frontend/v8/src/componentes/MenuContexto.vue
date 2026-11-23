<template>
  <ContextMenuRoot v-model:open="aberto">
    <ContextMenuTrigger
      as="div"
      class="v8-menu-contexto-alvo"
    >
      <slot />
    </ContextMenuTrigger>
    <ContextMenuPortal>
      <ContextMenuContent class="v8-suspenso">
        <template
          v-for="(item, posicao) in itens"
          :key="item.valor ?? `${posicao}`"
        >
          <ContextMenuSeparator
            v-if="item.separador"
            class="v8-suspenso-separador"
          />
          <ContextMenuLabel
            v-else-if="item.titulo"
            class="v8-suspenso-titulo"
          >
            {{ item.titulo }}
          </ContextMenuLabel>
          <ContextMenuItem
            v-else
            class="v8-suspenso-item"
            :class="{ 'v8-suspenso-item-perigo': item.perigo }"
            :disabled="item.desabilitado"
            @select="emit('selecionar', item.valor)"
          >
            {{ item.rotulo }}
          </ContextMenuItem>
        </template>
      </ContextMenuContent>
    </ContextMenuPortal>
  </ContextMenuRoot>
</template>

<script setup>
// Menu de contexto (docs/specs/v8/componentes.md), sobre o ContextMenu do Reka UI: abre com o
// botão direito (ou toque longo) sobre o conteúdo do slot. Os itens seguem o formato do
// `MenuSuspenso`, e escolher um emite `selecionar`.
//
//   <MenuContexto :itens="acoes" @selecionar="executar"><div class="v8-cartao">...</div></MenuContexto>

// 1. Imports
import {
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuPortal,
  ContextMenuRoot,
  ContextMenuSeparator,
  ContextMenuTrigger
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  }
})
const emit = defineEmits(['selecionar'])
const aberto = defineModel('open', { type: Boolean, default: false })
</script>
