<template>
  <div :class="['cronometro-component', css_class]">
    <div v-if="cronometro" :class="['croncard', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']">
      <div class="inner" @click="getCronometro">
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
import workerTimer from '@/timer/worker-timer'

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
      id: this.cronometro_id,
      ws: `/ws/cronometro/${this.cronometro_id}/`,
      app: 'painelset',
      model: 'cronometro',
      wsSocket: null,
      cronometro: null,
      instance: null,
      idInterval: null,
      syncInterval: 30, // sincroniza o cronômetro a cada 30 segundos
      countInterval: 0,
      debug_verbose: false,
      wait_destroy: false,
      display: this.display_initial, // 'elapsed', 'remaining', 'last_paused'
      modesDisplay: ['elapsed', 'remaining', 'last_paused'], // modos disponíveis
      timerInterval: 1500
    }
  },
  mounted: function () {
    console.log('Cronometro mounted, connecting to WebSocket:', this.ws, this.auto_start)
    this.$nextTick(() => {
      this.ws_client_cronometro()
      this.runInterval()
    })
  },
  watch: {
    cronometro_id: function (newVal, oldVal) {
      if (!this.nulls.includes(oldVal) && newVal !== oldVal && newVal > 0 && newVal !== this.id) {
        console.log('cronometrobase mudou de', oldVal, 'para', newVal)
        this.id = newVal
        this.ws = `/ws/cronometro/${this.cronometro_id}/`
        if (this.wsSocket) {
          this.wsSocket.close()
          this.wsSocket = null
        }
        this.cronometro = null
        this.ws_client_cronometro()
        this.runInterval()
      }
    }
  },
  beforeDestroy: function () {
    if (this.wsSocket) {
      console.log('Cronometro beforeDestroy, closing WebSocket')
      this.wsSocket.close()
      this.wsSocket = null
    }
    this.stopInterval()
  },
  methods: {
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
    ws_client_cronometro () {
      const t = this
      if (t.wsSocket) {
        t.wsSocket.close()
      }
      // conexão particular utilizando o WebSocket nativo
      t.wsSocket = new WebSocket(this.ws_endpoint())
      t.wsSocket.onmessage = this.handleWebSocketMessageLocal
      t.wsSocket.onopen = () => {
        // console.log('WebSocket conectado:', this.ws)
        if (t.auto_start) {
          t.startCronometro()
        } else {
          t.getCronometro()
        }
      }
      t.wsSocket.onclose = () => {
        console.log('WebSocket desconectado...')
        t.wsSocket = null
      }
      t.wsSocket.onerror = (error) => {
        console.error('Erro no WebSocket:', error)
        t.wsSocket = null
        t.ws_client_cronometro()
      }
      t.wsSocket.onpagehide = () => {
        console.log('WebSocket página oculta, fechando conexão')
        t.wsSocket.close()
      }
      t.wsSocket.onpageshow = () => {
        console.log('WebSocket página visível, reconectando')
        t.ws_client_cronometro()
      }
      return t.wsSocket
    },
    fetch (metadata) {
      const t = this
      if (metadata && metadata.hasOwnProperty('instance') && metadata.instance) {
        t.instance = metadata.instance
        t.cronometro = metadata.instance
        t.countInterval = t.syncInterval // força a sincronização na próxima iteração
      }
      t.refreshState(metadata)
        .then(obj => {
          if (obj.id === t.cronometro_id) {
            t.instance = obj
            t.cronometro = obj
            console.log(obj.state, obj.name)
          } else {
            t.instance = null
            t.cronometro = null
          }
        })
    },
    stopInterval () {
      if (this.idInterval) {
        this.wait_destroy = true
        workerTimer.clearInterval(this.idInterval)
        this.idInterval = null
      }
    },
    runInterval () {
      const t = this
      if (t.idInterval) {
        workerTimer.clearInterval(this.idInterval)
      }
      // Atualiza o cronômetro a cada segundo se estiver em execução
      t.idInterval = workerTimer.setInterval(() => {
        if (t.wait_destroy) {
          t.stopInterval()
          return
        }
        t.countInterval += 1
        if (t.countInterval >= t.syncInterval) {
          t.countInterval = 0
          t.getCronometro()
          return
        }
        if (t.cronometro && t.cronometro.state === 'running') {
          t.cronometro.elapsed_time = t.cronometro.elapsed_time + 1
          t.cronometro.remaining_time = t.cronometro.remaining_time - 1
          t.cronometro.accumulated_time = t.cronometro.accumulated_time + 1
        } else if (t.cronometro && t.cronometro.state === 'paused') {
          t.cronometro.last_paused_time = t.cronometro.last_paused_time + 1
        }
      }, 1000)
    },
    handleWebSocketMessageLocal (message) {
      // console.log('CRONÔMETRO: Mensagem recebida do WebSocket.')
      const data = JSON.parse(message.data)
      if (
        data.type === 'command_result' &&
        data.result && data.result.cronometro &&
        data.result.cronometro.id === this.cronometro_id
      ) {
        this.instance = data.result.cronometro
        this.cronometro = this.instance
        this.$emit(`cronometro_${data.command}`, this.cronometro)
        // console.log('command:', data.command, 'cronometro:', this.cronometro)
        if (data.command === 'start') {
          this.display = this.display_initial
          console.log('Cronômetro iniciado:', data)
        } else if (data.command === 'pause') {
          this.display = 'last_paused'
          console.log('Cronômetro pausado:', data)
        } else if (data.command === 'stop') {
          this.display = 'elapsed'
          console.log('Cronômetro parado:', data)
        } else if (data.command === 'resume') {
          this.display = this.display_initial
          console.log('Cronômetro retomado:', data)
        } else if (data.command === 'get') {
          // console.log('Estado do cronômetro atualizado:', data)
        }
        this.runInterval()
      }
    },
    addTime (seconds) {
      try {
        this.wsSocket.send(JSON.stringify({
          command: 'add_time',
          cronometro_id: this.cronometro.id,
          seconds: seconds
        }))
      } catch (error) {
        console.error('Erro ao enviar comando add_time:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    startCronometro () {
      try {
        this.wsSocket.send(JSON.stringify({
          command: 'start',
          cronometro_id: this.cronometro_id
        }))
      } catch (error) {
        console.error('Erro ao enviar comando start:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    pauseCronometro () {
      try {
        this.wsSocket.send(JSON.stringify({
          command: 'pause',
          cronometro_id: this.cronometro.id
        }))
      } catch (error) {
        console.error('Erro ao enviar comando pause:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    resumeCronometro () {
      try {
        this.wsSocket.send(JSON.stringify({
          command: 'resume',
          cronometro_id: this.cronometro.id
        }))
      } catch (error) {
        console.error('Erro ao enviar comando resume:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    stopCronometro () {
      try {
        this.wsSocket.send(JSON.stringify({
          command: 'stop',
          cronometro_id: this.cronometro.id
        }))
      } catch (error) {
        console.error('Erro ao enviar comando stop:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    getCronometro () {
      console.log(this.cronometro_id, 'Buscando estado atual do cronômetro no servidor...')
      try {
        if (!this.wsSocket) {
          this.ws_client_cronometro()
        } else {
          this.wsSocket.send(JSON.stringify({
            command: 'get',
            cronometro_id: this.cronometro_id
          }))
        }
      } catch (error) {
        console.error('Erro ao enviar comando get:', error)
        this.wsSocket = null
        this.ws_client_cronometro()
      }
    },
    secondsToTime: function (cronometro, timeKey, alternativeKey) {
      /* if (cronometro.id === 47) {
        console.log('entrou aqui 0', cronometro, timeKey, alternativeKey)
      }
      if (
        !cronometro ||
        (this.nulls.includes(cronometro[timeKey]) && alternativeKey === undefined) ||
        (alternativeKey !== undefined && this.nulls.includes(cronometro[alternativeKey]))
      ) {
        console.log('entrou aqui 1', cronometro, timeKey, alternativeKey)
        return '00:00'
      } */
      let totalSeconds = Math.round(
        cronometro[timeKey] || cronometro[alternativeKey] || 0
      )
      /* if (this.nulls.includes(totalSeconds)) {
        console.log('entrou aqui 2', cronometro, timeKey, alternativeKey)
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
