<template>
  <div
    class="painelset-painelvisao"
    :style="painelvisaoSelected?.styles.container || {}"
  >
    <div
      v-if="painelvisaoSelected?.config?.displayTitle"
      class="painelvisao-titulo"
      :style="painelvisaoSelected?.styles.title || {}"
    >
      {{ painelvisaoSelected?.name }}
    </div>
    <div
      class="inner-painelvisao"
      :style="painelvisaoSelected?.styles.inner || {}"
    >
      {{ painelvisaoSelected }}
    </div>
  </div>
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
  painelvisaoSelected: {
    type: Number,
    default: 0
  }
})

const painelvisaoSelected = computed(() => {
  return syncStore.data_cache.painelset_painelvisao?.[props.painelvisaoSelected] || null
})
</script>

<style lang="scss" scoped>
  .painelset-painelvisao {
    display: flex;
    overflow: hidden;
    flex-direction: column;
    justify-content: stretch;
    .inner-painelvisao {
      display: flex;
      flex: 1 1 100%;
      padding: 10px;
      overflow: auto;
    }
  }
</style>
