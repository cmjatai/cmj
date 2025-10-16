<template>
  <slot />
  <DisplayMessage />
</template>
<script setup>
import DisplayMessage from '~@/modules/messages/components/DisplayMessage'
import { useSyncStore } from '~@/stores/SyncStore'
const syncStore = useSyncStore()
syncStore.initialize()
</script>
