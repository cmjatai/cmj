<template>
  <MenubarRoot
    v-model="aberto"
    class="v8-barra-menus"
  >
    <MenubarMenu
      v-for="menu in menus"
      :key="menu.valor"
      :value="menu.valor"
    >
      <MenubarTrigger class="v8-barra-menus-gatilho">
        {{ menu.rotulo }}
      </MenubarTrigger>
      <MenubarPortal>
        <MenubarContent
          class="v8-suspenso"
          :side-offset="4"
        >
          <template
            v-for="(item, posicao) in menu.itens"
            :key="item.valor ?? `${posicao}`"
          >
            <MenubarSeparator
              v-if="item.separador"
              class="v8-suspenso-separador"
            />
            <MenubarLabel
              v-else-if="item.titulo"
              class="v8-suspenso-titulo"
            >
              {{ item.titulo }}
            </MenubarLabel>
            <MenubarItem
              v-else
              class="v8-suspenso-item"
              :class="{ 'v8-suspenso-item-perigo': item.perigo }"
              :disabled="item.desabilitado"
              @select="emit('selecionar', item.valor)"
            >
              {{ item.rotulo }}
            </MenubarItem>
          </template>
        </MenubarContent>
      </MenubarPortal>
    </MenubarMenu>
  </MenubarRoot>
</template>

<script setup>
// Barra de menus (docs/specs/v8/componentes.md), sobre o Menubar do Reka UI: menus de aplicativo
// lado a lado. Cada menu é `{ valor, rotulo, itens }`, e os itens seguem o formato do
// `MenuSuspenso`. Escolher um item emite `selecionar` com o valor dele.
//
//   <BarraMenus :menus="menus" @selecionar="executar" />

// 1. Imports
import {
  MenubarContent,
  MenubarItem,
  MenubarLabel,
  MenubarMenu,
  MenubarPortal,
  MenubarRoot,
  MenubarSeparator,
  MenubarTrigger
} from 'reka-ui'

// 3. Props & Emits
defineProps({
  menus: {
    type: Array,
    required: true
  }
})
const emit = defineEmits(['selecionar'])
// O `valor` do menu aberto, ou vazio.
const aberto = defineModel({ type: String, default: '' })
</script>
