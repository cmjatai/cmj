<template>
  <div
    ref="painelsetWidgetEditor"
    :key="`painelset-widget-editor-${widgetSelected?.id}`"
    class="'painelset-widget-editor"
  >
    Editor for widget {{ widgetSelected?.id }}
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed, ref } from 'vue'
import Resource from '~@/utils/resources'

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

const painelsetWidgetEditor = ref(null)

const widgetSelected = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const styleCoords = computed(() => {
  if (!widgetSelected.value || !widgetSelected.value.config?.coords) {
    return {}
  }
  const styles = {}
  const coords = widgetSelected.value.config.coords
  if (coords.x !== undefined) {
    styles.left = `${coords.x}%`
  }
  if (coords.y !== undefined) {
    styles.top = `${coords.y}%`
  }
  if (coords.w !== undefined) {
    styles.right = `${(coords.w + coords.x) > 100 ? 0 : 100 - (coords.w + coords.x)}%`
  }
  if (coords.h !== undefined) {
    styles.bottom = `${(coords.h + coords.y) > 100 ? 0 : 100 - (coords.h + coords.y)}%`
  }
  return styles
})

const childList = computed(() => {
  return _.orderBy(
    _.filter(syncStore.data_cache.painelset_widget, { parent: props.widgetSelected } ) || [],
    ['position'],
    ['asc']
  )
})

const syncChildList = async () => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'widget',
      filters: {
        parent: props.widgetSelected
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        // Process the fetched widgets
      }
    })
}

syncChildList()

</script>

<style lang="scss" scoped>
.painelset-widget-editor {

}
</style>
