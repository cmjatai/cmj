<template>
  <div
    class="widget-html-code"
    v-html="widgetSelected?.description || ''"
  />
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  },
})

const widgetSelected = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

</script>
<style lang="scss" scoped>
  .widget-html-code {
    width: 100%;
    height: 100%;
  }
</style>
