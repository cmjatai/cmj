<template>
  <Teleport
    v-if="overlay.rodapeEl"
    :to="overlay.rodapeEl"
  >
    <div class="v8-overlay-rodape-acoes">
      <slot />
    </div>
  </Teleport>
  <div
    v-else
    class="v8-overlay-rodape-acoes"
  >
    <slot />
  </div>
</template>
<script setup>
// Leva as ações do conteúdo para o rodapé fixo do overlay (V8-OVL-031).

// 1. Imports
import { useOverlay } from '~@/overlays/useOverlay'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
