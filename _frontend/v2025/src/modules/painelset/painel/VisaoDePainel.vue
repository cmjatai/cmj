<template>
  <div
    class="painelset-visaodepainel"
    :style="visaoDePainelSelected?.styles.component || {}"
  >
    <div
      v-if="visaoDePainelSelected?.config?.displayTitle"
      class="visaodepainel-titulo"
      :style="visaoDePainelSelected?.styles.title || {}"
    >
      {{ visaoDePainelSelected?.name }}
    </div>
    <div
      class="inner-visaodepainel"
      :style="visaoDePainelSelected?.styles.inner || {}"
    >
      <Widget
        v-for="(widget, index) in widgetList"
        :key="`widget-${widget.id}-${index}`"
        :painel-id="painelId"
        :widget-selected="widget.id"
      />
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

import Widget from './Widget.vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  visaodepainelSelected: {
    type: Number,
    default: 0
  }
})

const visaoDePainelSelected = computed(() => {
  return syncStore.data_cache.painelset_visaodepainel?.[props.visaodepainelSelected] || null
})

const widgetList = computed(() => {
  return _.orderBy(
    _.filter(
      syncStore.data_cache.painelset_widget,
      { visao: props.visaodepainelSelected, parent: null }
    ) || [],
    ['position'],
    ['asc']
  )
})

const syncWidgetList = async () => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'widget',
      filters: {
        visaodepainel: props.visaodepainelSelected
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        // Process the fetched widgets
      }
    })
}

syncWidgetList()

</script>

<style lang="scss" scoped>
  .painelset-visaodepainel {
    display: flex;
    flex-direction: column;
    flex: 1 1 100%;
    .inner-visaodepainel {
      position: relative;
      flex-direction: column;
      flex: 1 1 100%;
    }
  }
</style>
