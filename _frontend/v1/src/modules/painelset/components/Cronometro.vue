<template>
  <div :class="['cronometro-component', css_class]">
    <div v-if="cronometro" class="box">
      <div class="inner">
        {{ displayTime }}
        <div class="inner-rodape">
          <div v-if="display === 'elapsed'">
            <small>Tempo Decorrido</small>
          </div>
          <div v-else-if="display === 'remaining'">
            <small>Tempo Restante</small>
          </div>
        </div>
      </div>
      <div :class="['controls', css_class_controls]" v-if="css_class_controls">
        <div class="btn-group btn-group-sm" role="group" aria-label="First group">
          <a class="btn btn-outline-dark" @click.stop="toogleDisplay" title="Alternar exibição">
            <i class="fa fa-exchange-alt" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="startCronometro" v-if="cronometro.state === 'stopped'">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="pauseCronometro" v-if="cronometro.state === 'running'">
            <i class="fa fa-pause" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="resumeCronometro" v-if="cronometro.state === 'paused'">
            <i class="fa fa-play" aria-hidden="true"></i>
          </a>
          <a class="btn btn-outline-dark" @click.stop="stopCronometro" v-if="['running', 'paused'].includes(cronometro.state)">
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
<style>
.cronometro-component {
  .box {
    .inner {
      cursor: pointer;
      line-height: 1;
      .inner-rodape {
        font-size: 0.5em;
        text-align: center;
        margin-top: -3px;
        color: #ccc;
      }
    }
    .controls {
      margin-top: -5%;
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
<script>
import workerTimer from '@/timer/worker-timer'

export default {
  name: 'cronometro',
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
      display: 'elapsed', // 'elapsed', 'remaining'
      modesDisplay: ['elapsed', 'remaining'] // modos disponíveis
    }
  },
  mounted: function () {
    console.log('Cronometro mounted, connecting to WebSocket:', this.ws)
    this.ws_client_cronometro()
  },
  beforeDestroy: function () {
    if (this.wsSocket) {
      console.log('Cronometro beforeDestroy, closing WebSocket')
      this.wsSocket.close()
    }
    if (this.idInterval) {
      workerTimer.clearInterval(this.idInterval)
    }
  },
  methods: {
    toogleDisplay () {
      const currentIndex = this.modesDisplay.indexOf(this.display)
      const nextIndex = (currentIndex + 1) % this.modesDisplay.length
      this.display = this.modesDisplay[nextIndex]
    },
    ws_client_cronometro () {
      const t = this
      if (t.wsSocket) {
        t.wsSocket.close()
      }
      // conexão particular utilizando o WebSocket nativo
      t.wsSocket = new WebSocket(this.ws_endpoint())
      t.wsSocket.onopen = () => {
        console.log('WebSocket conectado:', this.ws)
      }
      t.wsSocket.onmessage = this.handleWebSocketMessageLocal
      t.wsSocket.onclose = () => {
        console.log('WebSocket desconectado...')
      }
      t.wsSocket.onerror = (error) => {
        console.error('Erro no WebSocket:', error)
        t.wsSocket.close()
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
        }
        this.countInterval += 1
        if (this.countInterval >= this.syncInterval) {
          this.getCronometro()
          this.countInterval = 0
        }
      }, 1000)
    },
    handleWebSocketMessageLocal (message) {
      console.log('Mensagem recebida do WebSocket:')
      const data = JSON.parse(message.data)
      if (
        data.type === 'command_result' &&
        data.result && data.result.cronometro &&
        data.result.cronometro.id === this.cronometro_id
      ) {
        this.cronometro = { ...this.cronometro, ...data.result.cronometro }
        if (data.command === 'start') {
          console.log('Cronômetro iniciado:', data)
        } else if (data.command === 'pause') {
          console.log('Cronômetro pausado:', data)
        } else if (data.command === 'stop') {
          console.log('Cronômetro parado:', data)
        } else if (data.command === 'resume') {
          console.log('Cronômetro retomado:', data)
        } else if (data.command === 'get') {
          console.log('Estado do cronômetro atualizado:', data)
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
    }
  },
  computed: {
    displayTime: function () {
      if (this.display === 'elapsed') {
        return this.elapsedTime
      } else if (this.display === 'remaining') {
        return this.remainingTime
      } else {
        return '00:00:00'
      }
    },
    elapsedTime: function () {
      // converte segundos para formato HH:MM:SS
      if (!this.cronometro || this.cronometro.elapsed_time == null) {
        return '00:00:00'
      }
      const totalSeconds = Math.round(this.cronometro.elapsed_time)
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      return [hours, minutes, seconds]
        .map(v => v < 10 ? '0' + v : v)
        .join(':') // "HH:MM:SS"
    },
    remainingTime: function () {
      // converte segundos para formato HH:MM:SS
      if (!this.cronometro || this.cronometro.remaining_time == null) {
        return '00:00:00'
      }
      const totalSeconds = Math.round(this.cronometro.remaining_time)
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      return [hours, minutes, seconds]
        .map(v => v < 10 ? '0' + v : v)
        .join(':') // "HH:MM:SS"
    },
    accumulatedTime: function () {
      // converte segundos para formato HH:MM:SS
      if (!this.cronometro || this.cronometro.accumulated_time == null) {
        return '00:00:00'
      }
      const totalSeconds = Math.round(this.cronometro.accumulated_time)
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60
      return [hours, minutes, seconds]
        .map(v => v < 10 ? '0' + v : v)
        .join(':') // "HH:MM:SS"
    }
  }
}
</script>
