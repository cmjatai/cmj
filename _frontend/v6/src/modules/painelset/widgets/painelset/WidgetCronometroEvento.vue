<template>
  <div
    class="widget-cronometro-evento"
  >
    <WidgetCronometroBase
      v-if="evento?.cronometro"
      :painel-id="painelId"
      :widget-selected="widgetSelected"
      :cronometro-id="evento?.cronometro"
    />
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

import WidgetCronometroBase from './WidgetCronometroBase.vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  }
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const evento = computed(() => {
  return syncStore.data_cache.painelset_evento
    ?.[painel.value?.evento] || null
})

</script>
<style lang="scss" scoped>
  .widget-cronometro-evento {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
