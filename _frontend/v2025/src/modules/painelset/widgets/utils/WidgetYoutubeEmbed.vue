<template>
  <div
    class="widget-iframe"
  >
    <iframe
      :width="props.width"
      :height="props.height"
      :src="srcIframeUrl"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      referrerpolicy="strict-origin-when-cross-origin"
      allowfullscreen
    />
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
  widgetSelected: {
    type: Number,
    default: 0
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '100%'
  },
  autoplay: {
    type: Number,
    default: 1
  }
})

const widgetSelected = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const srcIframeUrl = computed(() => {
  const paramsWidget = new URLSearchParams()
  _.each(widgetSelected.value?.config?.params || {}, (value, key) => {
    paramsWidget.append(key, value)
  })
  if (!widgetSelected.value?.config?.params.autoplay) {
    paramsWidget.append('autoplay', props.autoplay.toString())
  }
  const videoId = widgetSelected.value?.description.match(/(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1]
  return videoId ? `https://www.youtube.com/embed/${videoId}?${paramsWidget.toString()}` : (widgetSelected.value?.description || '')
})

</script>
<style lang="scss" scoped>
  .widget-iframe {
    width: 100%;
    height: 100%;
  }
</style>
