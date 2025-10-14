<template>
  <slot />
  <DisplayMessage />
  syncStore.state: {{ syncStore.data_cache.painelset_cronometro }} <br />
</template>
<script setup>
import DisplayMessage from '~@/components/utils/message/DisplayMessage'
import { useSyncStore } from '~@/js/stores/SyncStore'

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
