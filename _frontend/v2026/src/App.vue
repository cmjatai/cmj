<template>
  <slot />
  <DisplayMessage />

  <div
    id="modalCmj"
    ref="modalCmj"
  />
</template>
<script setup>

// 1. Imports
import DisplayMessage from '~@/modules/messages/components/DisplayMessage'
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { ref } from 'vue'

// 2. Composables
const syncStore = useSyncStore()
syncStore.initialize()

const authStore = useAuthStore()
authStore.loginStatus()

const modalCmj = ref(null)

// 3. Props & Emits
// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
