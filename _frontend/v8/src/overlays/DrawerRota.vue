<template>
  <RouterView v-slot="{ Component, route }">
    <OverlayFrame
      v-if="Component"
      :key="registro(route)?.path"
      kind="drawer"
      source="rota"
      :chave="registro(route)?.path"
      :opcoes="opcoes(route)"
      @fechar="voltarAoPai(route)"
    >
      <component :is="Component" />
    </OverlayFrame>
  </RouterView>
</template>
<script setup>
// Drawer guardado na rota (V8-OVL-053). Vai no componente da rota pai, no lugar do <RouterView>:
// a rota filha é desenhada dentro de um drawer, e fechar leva de volta à rota pai. As opções do
// drawer vêm de `meta.drawer` da rota filha. As rotas envolvidas precisam ter `name`.

// 1. Imports
import { inject } from 'vue'
import { RouterView, useRouter, viewDepthKey } from 'vue-router'
import { paramsDoRegistro } from '~@/core/router'
import OverlayFrame from '~@/overlays/OverlayFrame.vue'

// 2. Composables
const router = useRouter()
const profundidade = inject(viewDepthKey, 0)

// 3. Props & Emits
// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
function nivel() {
  return typeof profundidade === 'number' ? profundidade : profundidade.value
}

function registro(route) {
  return route.matched[nivel()] || null
}

function opcoes(route) {
  const meta = registro(route)?.meta || {}
  return { side: 'right', size: 'md', ...(meta.drawer || {}), title: meta.drawer?.title || meta.title || '' }
}

function voltarAoPai(route) {
  const pai = route.matched[nivel() - 1]
  if (pai?.name) {
    router.push({ name: pai.name, params: paramsDoRegistro(pai, route.params), query: route.query })
  } else {
    router.back()
  }
}
</script>
