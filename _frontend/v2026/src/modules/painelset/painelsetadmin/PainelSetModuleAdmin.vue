<template>
  <div class="painelset-module-admin online-module">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, nextTick } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

onMounted(() => {
  nextTick(() => {
    syncStore.registerModels('painelset', ['evento', 'cronometro', 'individuo'])
  })
})
</script>

<style lang="scss">
.painelset-module-admin {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  user-select: none;
}
</style>
