<template>
  <Teleport
    v-if="alvo"
    :to="alvo"
  >
    <RouterView />
  </Teleport>
  <Teleport
    v-if="trilha && niveis.length"
    :to="trilha"
  >
    <li
      v-for="(nivel, i) in niveis"
      :key="nivel.caminho"
      :aria-current="i === niveis.length - 1 ? 'page' : undefined"
    >
      <template v-if="i === niveis.length - 1">
        {{ nivel.rotulo }}
      </template>
      <RouterLink
        v-else
        :to="nivel.caminho"
      >
        {{ nivel.rotulo }}
      </RouterLink>
    </li>
  </Teleport>
</template>
<script setup>
// Saída da zona SPA (V8-ARQ-037): põe o <RouterView> no elemento [data-vue-zone] que o Django
// entregou e acrescenta à trilha do servidor os níveis da rota atual (V8-SHELL-022).

// 1. Imports
import { computed, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import pinia from '~@/core/pinia'
import { nomeDaRotaDaZona, paramsDoRegistro } from '~@/core/router'
import { useGlobalStore } from '~@/stores/GlobalStore'

// 2. Composables
const global = useGlobalStore(pinia)
const router = useRouter()
const route = useRoute()

// 3. Props & Emits
// 4. State & Refs
const nomeDaRota = global.zona ? nomeDaRotaDaZona(global.zona) : null
// Sem as rotas da zona, o HTML de espera do servidor fica no lugar.
const alvo = nomeDaRota && router.hasRoute(nomeDaRota) ? document.querySelector('[data-vue-zone]') : null
const trilha = alvo ? document.querySelector('[data-v8-trilha]') : null
const ultimoDoServidor = trilha?.querySelector('li[aria-current="page"]') || null

if (alvo) {
  alvo.replaceChildren()
}

// 5. Computed Properties
const niveis = computed(() => {
  if (!alvo) {
    return []
  }
  return route.matched
    .filter(registro => registro.meta?.breadcrumb)
    .map(registro => ({
      rotulo: registro.meta.breadcrumb,
      caminho: router.resolve({ name: registro.name, params: paramsDoRegistro(registro, route.params) }).path
    }))
})

// 6. Watchers
// O último item do servidor só é a página atual quando a zona não acrescenta níveis.
watch(niveis, valor => {
  if (!ultimoDoServidor) {
    return
  }
  if (valor.length) {
    ultimoDoServidor.removeAttribute('aria-current')
  } else {
    ultimoDoServidor.setAttribute('aria-current', 'page')
  }
}, { immediate: true })

// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
