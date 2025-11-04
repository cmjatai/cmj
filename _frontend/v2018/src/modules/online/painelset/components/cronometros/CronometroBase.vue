<template>
  <div :class="['cronometro-component', css_class]">
    <div v-if="cronometro" :class="['croncard', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']">
      <div class="inner">
        <div :class="['display-time', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']"
          :style="{ fontSize: display_size }">
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
      <div :class="['controls', css_class_controls]" v-if="css_class_controls">
        <div class="btn-group btn-group-sm" role="group" aria-label="First group">
          <a class="btn btn-outline-dark btn-toggle" @click.stop="toogleDisplay" title="Alternar exibição" v-if="controls.includes('toggleDisplay')">
            <i class="fa fa-exchange-alt" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark btn-start" @click.stop="startCronometro" v-if="cronometro.state === 'stopped' && controls.includes('start')">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark btn-pause" @click.stop="pauseCronometro" v-if="cronometro.state === 'running' && controls.includes('pause')">
            <i class="fa fa-pause" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark btn-resume" @click.stop="resumeCronometro" v-if="cronometro.state === 'paused' && controls.includes('resume')">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark btn-stop" @click.stop="stopCronometro" v-if="['running', 'paused'].includes(cronometro.state) && controls.includes('stop')">
            <i class="fa fa-stop" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark btn-negative btn-add1m" @click.stop="addTime(-60)" title="Reduzir 1 minuto" v-if="controls.includes('add1m')">
            -1m
          </a>
          <a class="btn btn-outline-dark btn-negative btn-add30s" @click.stop="addTime(-30)" title="Reduzir 30 segundos" v-if="controls.includes('add30s')">
            -30s
          </a>
          <a class="btn btn-outline-dark btn-add30s" @click.stop="addTime(30)" title="Adicionar 30 segundos" v-if="controls.includes('add30s')">
            +30s
          </a>
          <a class="btn btn-outline-dark btn-add1m" @click.stop="addTime(60)" title="Adicionar 1 minuto" v-if="controls.includes('add1m')">
            +1m
          </a>
          <a class="btn btn-outline-dark btn-add3m" @click.stop="addTime(180)" title="Adicionar 3 minutos" v-if="controls.includes('add3m')">
            +3m
          </a>
          <a class="btn btn-outline-dark btn-add5m" @click.stop="addTime(300)" title="Adicionar 5 minutos" v-if="controls.includes('add5m')">
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
<script>
import Vuex from 'vuex'
export default {
  name: 'cronometro-base',
  props: {
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
      default: 'elapsed', // 'elapsed', 'remaining', 'last_paused'
      validator: function (value) {
        return ['elapsed', 'remaining', 'last_paused'].includes(value)
      }
    },
    display_format: {
      type: String,
      default: 'hh:mm:ss' // Formato padrão de exibição
    },
    display_size: {
      type: String,
      default: '1.5em' // Tamanho padrão da fonte
    },
    auto_start: {
      type: Boolean,
      default: false // Iniciar automaticamente ao montar
    },
    auto_stop: {
      type: Boolean,
      default: false // Parar automaticamente ao destruir
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
      ] // Controles padrão
    }
  },
  data () {
    return {
      display: this.display_initial, // 'elapsed', 'remaining', 'last_paused'
      modesDisplay: ['elapsed', 'remaining', 'last_paused'], // modos disponíveis
      timerInterval: 1500,
      controlsDisplay: this.controls
    }
  },
  mounted: function () {
  },
  methods: {
    ...Vuex.mapActions('store__sync', ['sendSyncMessage']),
    toogleDisplay () {
      const currentIndex = this.modesDisplay.indexOf(this.display)
      const nextIndex = (currentIndex + 1) % this.modesDisplay.length
      let display = this.modesDisplay[nextIndex]
      if (display === 'last_paused' && this.cronometro.state !== 'paused') {
        // se o cronômetro não está pausado, não faz sentido mostrar o último tempo pausado
        display = 'elapsed' // volta para o início
      }
      this.display = display
    },
    addTime (seconds) {
      this.sendSyncMessage({
        type: 'command',
        command: 'add_time',
        app: 'painelset',
        model: 'cronometro',
        params: {
          id: this.cronometro_id,
          seconds: seconds
        }
      })
    },
    startCronometro () {
      this.sendSyncMessage({
        type: 'command',
        command: 'start',
        app: 'painelset',
        model: 'cronometro',
        params: {
          id: this.cronometro_id
        }
      })
      this.display = this.display_initial
      this.$emit('cronometro_start')
    },
    pauseCronometro () {
      this.sendSyncMessage({
        type: 'command',
        command: 'pause',
        app: 'painelset',
        model: 'cronometro',
        params: {
          id: this.cronometro_id
        }
      })
      this.display = 'last_paused'
      this.$emit('cronometro_pause')
    },
    resumeCronometro () {
      this.sendSyncMessage({
        type: 'command',
        command: 'resume',
        app: 'painelset',
        model: 'cronometro',
        params: {
          id: this.cronometro_id
        }
      })
      this.display = this.display_initial
      this.$emit('cronometro_resume')
    },
    stopCronometro () {
      this.sendSyncMessage({
        type: 'command',
        command: 'stop',
        app: 'painelset',
        model: 'cronometro',
        params: {
          id: this.cronometro_id
        }
      })
      this.display = 'elapsed'
    },
    secondsToTime: function (cronometro, timeKey, alternativeKey) {
      /* if (cronometro.id === 47) {
        console.debug('entrou aqui 0', cronometro, timeKey, alternativeKey)
      }
      if (
        !cronometro ||
        (this.nulls.includes(cronometro[timeKey]) && alternativeKey === undefined) ||
        (alternativeKey !== undefined && this.nulls.includes(cronometro[alternativeKey]))
      ) {
        console.debug('entrou aqui 1', cronometro, timeKey, alternativeKey)
        return '00:00'
      } */
      let totalSeconds = Math.round(
        cronometro[timeKey] || cronometro[alternativeKey] || 0
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
      if (this.display_format === 'hh:mm:ss') {
        r = [hours, minutes, seconds]
          .map(v => v < 10 ? '0' + v : v)
          .join(':') // "HH:MM:SS"
      } else if (this.display_format === 'mm:ss') {
        r = [minutes + hours * 60, seconds]
          .map(v => v < 10 ? '0' + v : v)
          .join(':') // "MM:SS"
      } else if (this.display_format === 'ss') {
        r = (seconds + minutes * 60 + hours * 3600).toString() // "SS"
      }
      if (negative) {
        r = negative + r
      }
      return r || '00:00:00'
    }
  },
  computed: {
    cronometro: function () {
      if (this.data_cache?.painelset_cronometro) {
        return Object.values(this.data_cache.painelset_cronometro).find(i => i.id === this.cronometro_id)
      }
      return null
    },
    displayTime: function () {
      if (this.display === 'elapsed') {
        return this.elapsedTime
      } else if (this.display === 'remaining') {
        return this.remainingTime
      } else if (this.display === 'last_paused') {
        return this.lastPausedTime
      } else {
        return '00:00:00'
      }
    },
    lastPausedTime: function () {
      return this.secondsToTime(this.cronometro, 'last_paused_time')
    },
    elapsedTime: function () {
      return this.secondsToTime(this.cronometro, 'elapsed_time')
    },
    remainingTime: function () {
      return this.secondsToTime(this.cronometro, 'remaining_time', 'accumulated_time')
    },
    accumulatedTime: function () {
      return this.secondsToTime(this.cronometro, 'accumulated_time')
    }
  }
}
</script>

<style lang="scss">
.cronometro-component {
  z-index: 2;
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
