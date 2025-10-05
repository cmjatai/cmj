<template>
  <div :class="['cronometro-component', css_class]">
    <div v-if="cronometro" :class="['croncard', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']">
      <div class="inner">
        <div :class="['display-time', display, cronometro.state, cronometro.remaining_time < 0 ? 'exceeded' : '']">
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
          <a class="btn btn-outline-dark" @click.stop="toogleDisplay" title="Alternar exibição" v-if="controls.includes('toggleDisplay')">
            <i class="fa fa-exchange-alt" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="startCronometro" v-if="cronometro.state === 'stopped' && controls.includes('start')">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="pauseCronometro" v-if="cronometro.state === 'running' && controls.includes('pause')">
            <i class="fa fa-pause" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="resumeCronometro" v-if="cronometro.state === 'paused' && controls.includes('resume')">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="stopCronometro" v-if="['running', 'paused'].includes(cronometro.state) && controls.includes('stop')">
            <i class="fa fa-stop" aria-hidden="true"></i>
          </a>
        </div>
      </div>
    </div>
    <div v-else>
      <p>Carregando cronômetro...</p>
    </div>
    <div v-if="cronometro && debug_verbose">
      <br><br>
      <hr>
      <h3>{{ cronometro.name }}</h3>
      <p>Estado: {{ cronometro.state }}</p>
      <p>Duração: {{ cronometro.duration }}</p>
      <p>Tempo Decorrido: {{ elapsedTime }}</p>
      <p>Tempo Restante: {{ remainingTime }}</p>
      <p>Iniciado em: {{ cronometro.started_at }}</p>
      <p>Pausado em: {{ cronometro.paused_at }}</p>
      <p>Finalizado em: {{ cronometro.finished_at }}</p>
      <p>Número de Cronômetros Filhos: {{ cronometro.children_count }}</p>
      <hr>
      <button @click="startCronometro" :disabled="cronometro.state === 'running'">Iniciar</button>
      <button @click="pauseCronometro" :disabled="cronometro.state !== 'running'">Pausar</button>
      <button @click="resumeCronometro" :disabled="cronometro.state !== 'paused'">Retomar</button>
      <button @click="stopCronometro" :disabled="cronometro.state === 'stopped'">Parar</button>
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
    controls: {
      type: Array,
      default: () => ['start', 'pause', 'resume', 'stop', 'toggleDisplay']
    }
  },
  data () {
    return {
      ws: `/ws/cronometro/${this.cronometro_id}/`,
      wsSocket: null,
      cronometro: null,
      idInterval: null,
      syncInterval: 30, // sincroniza o cronômetro a cada 30 segundos
      countInterval: 0,
      debug_verbose: false,
      display: 'elapsed', // 'elapsed', 'remaining', 'last_paused'
      modesDisplay: ['elapsed', 'remaining', 'last_paused'] // modos disponíveis
    }
  },
  mounted: function () {
    // console.log('Cronometro mounted, connecting to WebSocket:', this.ws)
    this.ws_client_cronometro()
  },
  beforeDestroy: function () {
    if (this.wsSocket) {
      console.log('Cronometro beforeDestroy, closing WebSocket')
      this.wsSocket.close()
      this.wsSocket = null
    }
    if (this.idInterval) {
      workerTimer.clearInterval(this.idInterval)
    }
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
      }
      t.wsSocket.onclose = () => {
        console.log('WebSocket desconectado...')
        // tenta reconectar em 5 segundos
        setTimeout(() => {
          if (t.wsSocket) {
            t.ws_client_cronometro()
          }
        }, 5000)
      }
      t.wsSocket.onerror = (error) => {
        console.error('Erro no WebSocket:', error)
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
    runInterval () {
      if (this.idInterval) {
        workerTimer.clearInterval(this.idInterval)
      }
      // Atualiza o cronômetro a cada segundo se estiver em execução
      this.idInterval = workerTimer.setInterval(() => {
        if (this.cronometro && this.cronometro.state === 'running') {
          this.cronometro.elapsed_time = this.cronometro.elapsed_time + 1
          this.cronometro.remaining_time = this.cronometro.remaining_time - 1
          this.cronometro.accumulated_time = this.cronometro.accumulated_time + 1
        } else if (this.cronometro && this.cronometro.state === 'paused') {
          this.cronometro.last_paused_time = this.cronometro.last_paused_time + 1
        }
        this.countInterval += 1
        if (this.countInterval >= this.syncInterval) {
          this.getCronometro()
          this.countInterval = 0
        }
        this.refreshState({
          app: 'painelset',
          model: 'cronometro',
          id: this.cronometro_id,
          value: { ...this.cronometro }
        })
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
        this.cronometro = { ...this.cronometro, ...data.result.cronometro }
        this.$emit(`cronometro_${data.command}`, this.cronometro)
        // console.log('command:', data.command, 'cronometro:', this.cronometro)
        if (data.command === 'start') {
          this.display = 'elapsed'
          console.log('Cronômetro iniciado:', data)
        } else if (data.command === 'pause') {
          this.display = 'last_paused'
          console.log('Cronômetro pausado:', data)
        } else if (data.command === 'stop') {
          this.display = 'elapsed'
          console.log('Cronômetro parado:', data)
        } else if (data.command === 'resume') {
          this.display = 'elapsed'
          console.log('Cronômetro retomado:', data)
        } else if (data.command === 'get') {
          // console.log('Estado do cronômetro atualizado:', data)
        }
        this.runInterval()
      }
    },
    startCronometro () {
      this.wsSocket.send(JSON.stringify({
        command: 'start',
        cronometro_id: this.cronometro.id
      }))
    },
    pauseCronometro () {
      this.wsSocket.send(JSON.stringify({
        command: 'pause',
        cronometro_id: this.cronometro.id
      }))
    },
    resumeCronometro () {
      this.wsSocket.send(JSON.stringify({
        command: 'resume',
        cronometro_id: this.cronometro.id
      }))
    },
    stopCronometro () {
      this.wsSocket.send(JSON.stringify({
        command: 'stop',
        cronometro_id: this.cronometro.id
      }))
    },
    getCronometro () {
      // qual o estado atual do cronometro no servidor?
      this.wsSocket.send(JSON.stringify({
        command: 'get',
        cronometro_id: this.cronometro_id
      }))
    },
    secondsToTime: function (cronometro, timeKey, alternativeKey) {
      if (
        !cronometro ||
        (this.nulls.includes(cronometro[timeKey]) && alternativeKey === undefined) ||
        (alternativeKey !== undefined && this.nulls.includes(cronometro[alternativeKey]))
      ) {
        return '00:00:00'
      }
      let totalSeconds = Math.round(
        cronometro[timeKey] || cronometro[alternativeKey]
      )
      if (this.nulls.includes(totalSeconds)) {
        return '00:00:00'
      }
      if (totalSeconds < 0) {
        totalSeconds = totalSeconds * -1
      }
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      return [hours, minutes, seconds]
        .map(v => v < 10 ? '0' + v : v)
        .join(':') // "HH:MM:SS"
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
        font-size: 0.5em;
        text-align: center;
        font-style: italic;
      }
    }
    .display-time {
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
          color: rgb(255, 57, 245);  /* verde se em execução */
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
      z-index: 1;
      &.hover {
        position: absolute;
        top: 100%;
        display: none;
      }
    }
    &:hover .controls.hover {
      display: block;
    }
  }
}
</style>
