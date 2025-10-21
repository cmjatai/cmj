<template>
  <div
    :class="['widget-cronometro-base', display]"
  >
    {{ displayTime }}
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed, ref, onMounted } from 'vue'

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
  displayInitial: {
    type: String,
    default: 'elapsed', // 'elapsed', 'remaining', 'last_paused'
    validator: function (value) {
      return ['elapsed', 'remaining', 'last_paused'].includes(value)
    }
  },
  displayFormat: {
    type: String,
    default: 'hh:mm:ss' // Formato padrão de exibição
  },
  cronometroId: {
    type: Number,
    required: true
  }
})

const display = ref(props.displayInitial)

const cronometro = computed(() => {
  return syncStore.data_cache.painelset_cronometro
    ?.[props.cronometroId] || null
})

const syncCronometro = async () => {
  await syncStore.fetchSync({
    app: 'painelset',
    model: 'cronometro',
    id: props.cronometroId
  })
  .then(() => {
    console.log('Iniciando cronômetro localmente:', props.cronometroId)
    syncStore.startLocalCronometro(props.cronometroId)
  })
}

onMounted(() => {
  syncCronometro()
})

const secondsToTime = (timeKey, alternativeKey) => {
  let totalSeconds = Math.round(
    timeKey || alternativeKey || 0
  )
  /* if (this.nulls.includes(totalSeconds)) {
    console.debug('entrou aqui 2', cronometro, timeKey, alternativeKey)
    return '00:00'
  } */
  const negative = totalSeconds < 0 ? '-' : ''
  if (totalSeconds < 0) {
    totalSeconds = totalSeconds * -1
  }
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  let r = ''
  if (props.displayFormat === 'hh:mm:ss') {
    r = [hours, minutes, seconds]
      .map(v => v < 10 ? '0' + v : v)
      .join(':') // "HH:MM:SS"
  } else if (props.displayFormat === 'mm:ss') {
    r = [minutes + hours * 60, seconds]
      .map(v => v < 10 ? '0' + v : v)
      .join(':') // "MM:SS"
  } else if (props.displayFormat === 'ss') {
    r = (seconds + minutes * 60 + hours * 3600).toString() // "SS"
  }
  if (negative) {
    r = negative + r
  }
  return r || '00:00:00'
}

const displayTime = computed(() => {
  if (!cronometro.value) {
    return '00:00:00'
  }
  if (display.value === 'elapsed') {
    return secondsToTime(cronometro.value.elapsed_time)
  } else if (display.value === 'remaining') {
    return secondsToTime(cronometro.value.remaining_time, cronometro.value.accumulated_time)
  } else if (display.value === 'last_paused') {
    return secondsToTime(cronometro.value.last_paused_time)
  } else {
    return '00:00:00'
  }
})

</script>
<style lang="scss" scoped>
  .widget-cronometro-base {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
