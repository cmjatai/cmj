<!--
 componente Vue para exibir e controlar um cronômetro.
 fields:
 {"id":1,"__str__":"Cronômetro do Evento: Painel Geral de Sessões Ordinárias - Legislatura 2025/2028 (stopped)","link_detail_backend":"","elapsed_time":"0.0","remaining_time":"14400.0","children_count":0,"name":"Cronômetro do Evento: Painel Geral de Sessões Ordinárias - Legislatura 2025/2028","duration":"04:00:00","state":"stopped","created_at":"2025-10-01T16:00:12.433865-03:00","started_at":null,"paused_at":null,"finished_at":null,"pause_parent_on_start":false,"accumulated_time":"00:00:00","object_id":4,"parent":null,"content_type":319}

-->
<template>
  <div class="cronometro-component">
    <div v-if="cronometro">
      <h3>{{ cronometro.name }}</h3>
      <p>Estado: {{ cronometro.state }}</p>
      <p>Duração: {{ cronometro.duration }}</p>
      <p>Tempo Decorrido: {{ elapsedTime }}</p>
      <p>Tempo Restante: {{ remainingTime }}</p>
      <p>Tempo Acumulado: {{ accumulatedTime }}</p>
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
    <div v-else>
      <p>Carregando cronômetro...</p>
    </div>
  </div>
</template>
<script>
import workerTimer from '@/timer/worker-timer'

export default {
  name: 'cronometro',
  props: {
    cronometro_id: {
      type: Number,
      required: true
    }
  },
  data () {
    return {
      ws: `/ws/cronometro/${this.cronometro_id}/`,
      cronometro: null,
      id_interval: null
    }
  },
  computed: {
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
  },
  mounted: function () {
    console.log('Cronometro mounted, connecting to WebSocket:', this.ws)
    this.$options.sockets.onmessage = this.handleWebSocketMessageLocal
    this.ws_reconnect()
    this.restartInterval()
  },
  methods: {
    restartInterval () {
      if (this.id_interval) {
        workerTimer.clearInterval(this.id_interval)
      }
      // Atualiza o cronômetro a cada segundo se estiver em execução
      this.id_interval = workerTimer.setInterval(() => {
        if (this.cronometro && this.cronometro.state === 'running') {
          this.cronometro.elapsed_time = this.cronometro.elapsed_time + 1
          this.cronometro.remaining_time = this.cronometro.remaining_time - 1
        }
      }, 1000)
    },
    handleWebSocketMessageLocal (message) {
      const data = JSON.parse(message.data)
      if (data.type === 'cronometro_state' && data.cronometro.id === this.cronometro_id) {
        this.cronometro = { ...this.cronometro, ...data.cronometro }
      } else if (data.type === 'command_result') {
        this.cronometro = { ...this.cronometro, ...data.cronometro }
        if (data.command === 'start') {
          console.log('Cronômetro iniciado:', data)
        } else if (data.command === 'pause') {
          console.log('Cronômetro pausado:', data)
        } else if (data.command === 'stop') {
          console.log('Cronômetro parado:', data)
        }
        this.restartInterval()
      }
    },
    startCronometro () {
      this.$socket.send(JSON.stringify({
        command: 'start',
        cronometro_id: this.cronometro.id
      }))
    },
    pauseCronometro () {
      this.$socket.send(JSON.stringify({
        command: 'pause',
        cronometro_id: this.cronometro.id
      }))
    },
    resumeCronometro () {
      this.$socket.send(JSON.stringify({
        command: 'resume',
        cronometro_id: this.cronometro.id
      }))
    },
    stopCronometro () {
      this.$socket.send(JSON.stringify({
        command: 'stop',
        cronometro_id: this.cronometro.id
      }))
    }
  }
}
</script>
