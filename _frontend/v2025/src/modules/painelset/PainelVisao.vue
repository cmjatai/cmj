<template>
  <div class="painelset-painelvisao">
    painel-visao works!
    <div>Sync Store Cronometro: {{ syncStore.data_cache.painelset_cronometro }}</div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
const syncStore = useSyncStore()
syncStore.registerModels('painelset', ['cronometro'])
</script>
<style scoped>
</style>
