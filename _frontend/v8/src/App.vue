<template>
  <IslandHost />
  <ZoneOutlet />
  <OverlayHost />
  <ToastHost />
</template>
<script setup>
// Raiz do app único do v8. É montada em #cmj-v8-app, que o Django entrega vazio, e alcança o
// resto da página por Teleport: as ilhas, a zona SPA, os overlays e os toasts (V8-ARQ-031).

// 1. Imports
import IslandHost from '~@/core/IslandHost.vue'
import ZoneOutlet from '~@/core/ZoneOutlet.vue'
import OverlayHost from '~@/overlays/OverlayHost.vue'
import ToastHost from '~@/overlays/ToastHost.vue'

// 2. Composables
// 3. Props & Emits
// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
