<template>
  <div
    :class="['widget-cronometro-base', display, fases]"
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

const cronometro = computed(() => {
  return syncStore.data_cache.painelset_cronometro
    ?.[props.cronometroId] || null
})

const display = computed(() => {
  if (!cronometro.value) {
    return props.displayInitial
  }
  if (cronometro.value.state === 'running') {
    return props.displayInitial
  } else {
    return 'last_paused'
  }
})

const fases = computed(() => {
  // menor que zero retorna texto s0, menor que 10s retorna texto s10, menor que 30s retorna texto s30
  if (!cronometro.value) {
    return ''
  }
  if (cronometro.value.remaining_time < 0) {
    return 's00'
  } else if (cronometro.value.remaining_time <= 10) {
    return 's10'
  } else if (cronometro.value.remaining_time <= 30) {
    return 's30'
  } else {
    return ''
  }
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
  return r || '00:00'
}

const displayTime = computed(() => {
  if (!cronometro.value) {
    return '00:00'
  }
  if (display.value === 'elapsed') {
    return secondsToTime(cronometro.value.elapsed_time)
  } else if (display.value === 'remaining') {
    return secondsToTime(cronometro.value.remaining_time, cronometro.value.accumulated_time)
  } else if (display.value === 'last_paused') {
    return secondsToTime(cronometro.value.last_paused_time)
  } else {
    return '00:00'
  }
})

</script>
<style lang="scss" scoped>
@keyframes pulse {
    0% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 orange;
    }
    70% {
        transform: scale(1);
        box-shadow: 0 0 0 10px rgba(0, 123, 255, 0);
    }
    100% {
        transform: scale(0.9);
        box-shadow: 0 0 0 0 orange;
    }
}
  .widget-cronometro-base {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 1s ease;
    &.s00 {
      color: red;
      transform: scale(1.3);
    }
    &.s10 {
      color: orange;
      // pulse animation
      animation: pulse 1s infinite;
    }
    &.s30 {
      color: yellow;
    }
  }
</style>
