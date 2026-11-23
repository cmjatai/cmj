<template>
  <NavigationMenuRoot
    v-model="aberto"
    class="v8-menu-navegacao"
    :aria-label="rotulo || undefined"
  >
    <NavigationMenuList class="v8-menu-navegacao-lista">
      <NavigationMenuItem
        v-for="item in itens"
        :key="item.valor"
        class="v8-menu-navegacao-item"
        :value="item.valor"
      >
        <template v-if="item.links">
          <NavigationMenuTrigger class="v8-btn v8-btn-fantasma v8-menu-navegacao-gatilho">
            {{ item.rotulo }}
            <svg
              class="v8-icone v8-menu-navegacao-seta"
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
          </NavigationMenuTrigger>
          <NavigationMenuContent class="v8-menu-navegacao-painel">
            <ul class="v8-menu-navegacao-links">
              <li
                v-for="link in item.links"
                :key="link.href"
              >
                <NavigationMenuLink
                  class="v8-menu-navegacao-link"
                  :href="link.href"
                  :active="link.ativo"
                >
                  <span class="v8-menu-navegacao-link-titulo">{{ link.rotulo }}</span>
                  <span
                    v-if="link.descricao"
                    class="v8-menu-navegacao-link-descricao"
                  >{{ link.descricao }}</span>
                </NavigationMenuLink>
              </li>
            </ul>
          </NavigationMenuContent>
        </template>
        <NavigationMenuLink
          v-else
          class="v8-btn v8-btn-fantasma"
          :href="item.href"
          :active="item.ativo"
        >
          {{ item.rotulo }}
        </NavigationMenuLink>
      </NavigationMenuItem>
    </NavigationMenuList>
  </NavigationMenuRoot>
</template>

<script setup>
// Menu de navegação (docs/specs/v8/componentes.md), sobre o NavigationMenu do Reka UI: links
// diretos e grupos que abrem um painel com links. Item é `{ valor, rotulo, href, ativo }` ou
// `{ valor, rotulo, links: [{ rotulo, href, descricao, ativo }] }`. O link ativo sai com
// `aria-current="page"`.
//
//   <MenuNavegacao rotulo="Seções" :itens="secoes" />

// 1. Imports
import {
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuRoot,
  NavigationMenuTrigger
} from 'reka-ui'
import { ICONES } from '~@/componentes/icones'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  rotulo: {
    type: String,
    default: ''
  }
})
// O `valor` do grupo aberto, ou vazio.
const aberto = defineModel({ type: String, default: '' })
</script>
