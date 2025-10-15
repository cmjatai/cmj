<template>
  <slot />
  <DisplayMessage />
  syncStore.state: {{ syncStore.data_cache.painelset_cronometro }} <br>
  404 component test:
  <cmj-error-404 />
</template>
<script setup>
import DisplayMessage from '~@/modules/messages/components/DisplayMessage'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()
syncStore.initialize()
syncStore.registerModels(
  'painelset', [
    'evento',
    'individuo',
    'cronometro'
  ]
)
</script>
