<template>
  <div :class="['cronometro-component', css_class]">
    <div
      v-if="cronometro"
      :class="['croncard', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']"
    >
      <div class="inner">
        <div
          :class="['display-time', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']"
          :style="{ fontSize: display_size }"
        >
          {{ displayTime }}
        </div>
        <div class="inner-rodape">
          <div v-if="display === 'elapsed'">
            <small>Tempo Decorrido</small>
          </div>
          <div v-else-if="display === 'remaining'">
            <small v-if="cronometro.remaining_time < 0">Tempo Excedido</small>
            <small v-else>Tempo Restante</small>
          </div>
          <div v-else-if="display === 'last_paused'">
            <small>Tempo de Suspensão</small>
          </div>
        </div>
      </div>
      <div
        :class="['controls', css_class_controls]"
        v-if="css_class_controls"
      >
        <div
          class="btn-group btn-group-sm"
          role="group"
          aria-label="First group"
        >
          <a
            class="btn btn-outline-dark btn-toggle"
            @click.stop="toogleDisplay"
            title="Alternar exibição"
            v-if="controls.includes('toggleDisplay')"
          >
            <FontAwesomeIcon icon="exchange-alt" />
          </a>
          <a
            class="btn btn-outline-dark btn-start"
            @click.stop="startCronometro"
            v-if="cronometro.state === 'stopped' && controls.includes('start')"
          >
            <FontAwesomeIcon icon="play" />
          </a>
          <a
            class="btn btn-outline-dark btn-pause"
            @click.stop="pauseCronometro"
            v-if="cronometro.state === 'running' && controls.includes('pause')"
          >
            <FontAwesomeIcon icon="pause" />
          </a>
          <a
            class="btn btn-outline-dark btn-resume"
            @click.stop="resumeCronometro"
            v-if="cronometro.state === 'paused' && controls.includes('resume')"
          >
            <FontAwesomeIcon icon="play" />
          </a>
          <a
            class="btn btn-outline-dark btn-stop"
            @click.stop="stopCronometro"
            v-if="['running', 'paused'].includes(cronometro.state) && controls.includes('stop')"
          >
            <FontAwesomeIcon icon="stop" />
          </a>
          <a
            class="btn btn-outline-dark btn-negative btn-add1m"
            @click.stop="addTime(-60)"
            title="Reduzir 1 minuto"
            v-if="controls.includes('add1m')"
          >
            -1m
          </a>
          <a
            class="btn btn-outline-dark btn-negative btn-add30s"
            @click.stop="addTime(-30)"
            title="Reduzir 30 segundos"
            v-if="controls.includes('add30s')"
          >
            -30s
          </a>
          <a
            class="btn btn-outline-dark btn-add30s"
            @click.stop="addTime(30)"
            title="Adicionar 30 segundos"
            v-if="controls.includes('add30s')"
          >
            +30s
          </a>
          <a
            class="btn btn-outline-dark btn-add1m"
            @click.stop="addTime(60)"
            title="Adicionar 1 minuto"
            v-if="controls.includes('add1m')"
          >
            +1m
          </a>
          <a
            class="btn btn-outline-dark btn-add3m"
            @click.stop="addTime(180)"
            title="Adicionar 3 minutos"
            v-if="controls.includes('add3m')"
          >
            +3m
          </a>
          <a
            class="btn btn-outline-dark btn-add5m"
            @click.stop="addTime(300)"
            title="Adicionar 5 minutos"
            v-if="controls.includes('add5m')"
          >
            +5m
          </a>
        </div>
      </div>
    </div>
    <div v-else>
      <p>Carregando cronômetro...</p>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const emit = defineEmits(['cronometro_start', 'cronometro_pause', 'cronometro_resume'])

const props = defineProps({
  cronometro_id: {
    type: Number,
    required: true
  },
  css_class: {
    type: String,
    default: ''
  },
  css_class_controls: {
    type: String,
    default: ''
  },
  display_initial: {
    type: String,
    default: 'elapsed',
    validator: (value) => ['elapsed', 'remaining', 'last_paused'].includes(value)
  },
  display_format: {
    type: String,
    default: 'hh:mm:ss'
  },
  display_size: {
    type: String,
    default: '1.5em'
  },
  auto_start: {
    type: Boolean,
    default: false
  },
  auto_stop: {
    type: Boolean,
    default: false
  },
  controls: {
    type: Array,
    default: () => [
      'start',
      'pause',
      'resume',
      'stop',
      'add30s',
      'add1m',
      'add3m',
      'add5m',
      'toggleDisplay'
    ]
  }
})

const display = ref(props.display_initial)
const modesDisplay = ['elapsed', 'remaining', 'last_paused']

const cronometro = computed(() => {
  if (syncStore.data_cache?.painelset_cronometro) {
    return Object.values(syncStore.data_cache.painelset_cronometro).find(i => i.id === props.cronometro_id)
  }
  return null
})

const secondsToTime = (cron, timeKey, alternativeKey) => {
  let totalSeconds = Math.round(
    cron[timeKey] || cron[alternativeKey] || 0
  )
  const negative = totalSeconds < 0 ? '-' : ''
  if (totalSeconds < 0) {
    totalSeconds = totalSeconds * -1
  }
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  let r = ''
  if (props.display_format === 'hh:mm:ss') {
    r = [hours, minutes, seconds]
      .map(v => v < 10 ? '0' + v : v)
      .join(':')
  } else if (props.display_format === 'mm:ss') {
    r = [minutes + hours * 60, seconds]
      .map(v => v < 10 ? '0' + v : v)
      .join(':')
  } else if (props.display_format === 'ss') {
    r = (seconds + minutes * 60 + hours * 3600).toString()
  }
  if (negative) {
    r = negative + r
  }
  return r || '00:00:00'
}

const displayTime = computed(() => {
  if (display.value === 'elapsed') return elapsedTime.value
  if (display.value === 'remaining') return remainingTime.value
  if (display.value === 'last_paused') return lastPausedTime.value
  return '00:00:00'
})

const lastPausedTime = computed(() => secondsToTime(cronometro.value, 'last_paused_time'))
const elapsedTime = computed(() => secondsToTime(cronometro.value, 'elapsed_time'))
const remainingTime = computed(() => secondsToTime(cronometro.value, 'remaining_time', 'accumulated_time'))

const toogleDisplay = () => {
  const currentIndex = modesDisplay.indexOf(display.value)
  const nextIndex = (currentIndex + 1) % modesDisplay.length
  let d = modesDisplay[nextIndex]
  if (d === 'last_paused' && cronometro.value.state !== 'paused') {
    d = 'elapsed'
  }
  display.value = d
}

const addTime = (seconds) => {
  syncStore.sendSyncMessage({
    type: 'command',
    command: 'add_time',
    app: 'painelset',
    model: 'cronometro',
    params: {
      id: props.cronometro_id,
      seconds: seconds
    }
  })
}

const startCronometro = () => {
  syncStore.sendSyncMessage({
    type: 'command',
    command: 'start',
    app: 'painelset',
    model: 'cronometro',
    params: { id: props.cronometro_id }
  })
  display.value = props.display_initial
  emit('cronometro_start')
}

const pauseCronometro = () => {
  syncStore.sendSyncMessage({
    type: 'command',
    command: 'pause',
    app: 'painelset',
    model: 'cronometro',
    params: { id: props.cronometro_id }
  })
  display.value = 'last_paused'
  emit('cronometro_pause')
}

const resumeCronometro = () => {
  syncStore.sendSyncMessage({
    type: 'command',
    command: 'resume',
    app: 'painelset',
    model: 'cronometro',
    params: { id: props.cronometro_id }
  })
  display.value = props.display_initial
  emit('cronometro_resume')
}

const stopCronometro = () => {
  syncStore.sendSyncMessage({
    type: 'command',
    command: 'stop',
    app: 'painelset',
    model: 'cronometro',
    params: { id: props.cronometro_id }
  })
  display.value = 'elapsed'
}
</script>

<style lang="scss">
.cronometro-component {
  z-index: 1000;

  .btn-outline-dark {
    color: white;
    border-color: #777;
  }
  .croncard {
    display: flex;
    flex-direction: column;
    height: 100%;
    align-items: center;
    justify-content: center;
    background-color: #444;
    color: #fff;
    // border-radius: 8px;
    padding: 5px 10px 3px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    text-align: center;
    z-index: 100000;
    .inner {
      line-height: 1;
      flex-direction: column;
      justify-content: stretch;
      align-content: stretch;
      .inner-rodape {
        font-size: 0.8em;
        text-align: center;
        font-style: italic;
      }
    }
    .display-time {
      font-weight: bold;
      &.elapsed { /* tempo decorrido */
        &.running {
          color: #0f0;  /* verde se em execução */
          &.exceeded {
            color: #ffa500; /* laranja se em execução e excedeu o tempo */
          }
        }
        &.paused {
          color: #ff0;  /* amarelo se pausado */
          &.exceeded {
            color: #ffa500; /* laranja se pausado e excedeu o tempo */
          }
        }
        &.stopped {
          color: #ccc;  /* cinza claro se parado */
        }
      }
      &.remaining { /* tempo restante */
        &.running {
          color: #ff0;  /* verde se em execução */
          &.exceeded {
            color: #f00; /* vermelho se em execução e excedeu o tempo */
          }
        }
        &.paused {
          color: #ff0;  /* amarelo se pausado */
          &.exceeded {
            color: #f00; /* vermelho se pausado e excedeu o tempo */
          }
        }
      }
      &.last_paused { /* último tempo pausado */
        &.paused {
          color: #ff0;  /* amarelo se pausado */
        }
      }
      &.stopped {
        color: #ccc;  /* cinza claro se parado */
      }
    }
    .controls {
      z-index: 2;
      &.hover {
        position: absolute;
        top: 100%;
        margin-top: -3px;
        display: none;
      }
    }
    &:hover .controls.hover {
      display: block;
      z-index: 2;
    }
  }
}
</style>
