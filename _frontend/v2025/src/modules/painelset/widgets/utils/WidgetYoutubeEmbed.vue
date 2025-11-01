<template>
  <div
    class="widget-iframe"
  >
    <iframe v-if="srcIframeUrl"
      :width="props.width"
      :height="props.height"
      :src="srcIframeUrl"
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      referrerpolicy="strict-origin-when-cross-origin"
      allowfullscreen
    ></iframe>
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
const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})
const evento = computed(() => {
  return syncStore.data_cache.painelset_evento
    ?.[painel.value?.evento] || null
})

const srcIframeUrl = computed(() => {
  const paramsWidget = new URLSearchParams()
  _.each(widgetSelected.value?.config?.youtube?.params || {}, (value, key) => {
    paramsWidget.append(key, value)
  })
  if (!widgetSelected.value?.config?.youtube?.params.autoplay) {
    paramsWidget.append('autoplay', props.autoplay.toString())
  }
  let videoId = evento.value?.youtube_id || widgetSelected.value?.config?.youtube?.id || ''
  videoId = videoId ? `https://www.youtube.com/embed/${videoId}?${paramsWidget.toString()}` : ''
  console.log('videoId', videoId)
  return videoId

})

</script>
<style lang="scss" scoped>
  .widget-iframe {
    width: 100%;
    height: 100%;
  }
</style>
