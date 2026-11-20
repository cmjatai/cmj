<template>
  <div class="painelset-module-admin online-module">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, nextTick, inject } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()
const EventBus = inject('EventBus')

onMounted(() => {
  EventBus.emit('side:close-sideright')
  nextTick(() => {
    syncStore.registerModels('painelset', ['evento', 'cronometro', 'individuo'])
  })
})
</script>

<style lang="scss">
.painelset-module-admin {
  position: absolute;
  top: var(--header-height);
  left: var(--width-sidebar-collapsed);
  right: 0;
  bottom: 0;
  user-select: none;
}
</style>
