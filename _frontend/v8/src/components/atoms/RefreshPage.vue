<template>
  <div
    v-if="show"
    class="refresh-countdown"
  >
    <slot />... esta página atualizará em {{ displayTime }}.
  </div>
</template>

<script>
export default {
  name: 'RefreshPage',
  props: {
    timeout: {
      type: Number,
      required: true,
      validator: (value) => value > 0
    },
    show: {
      type: Boolean,
      required: true,
    },
    enabled: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      timer: null,
      remainingTime: 0
    }
  },
  computed: {
    displayTime() {
      const seconds = Math.ceil(this.remainingTime / 1000);
      return seconds > 0 ? `${seconds} segundos` : 'Agora';
    }
  },
  mounted() {
    if (this.enabled) {
      this.startTimer();
    }
  },
  beforeUnmount() {
    this.clearTimers();
  },
  watch: {
    enabled(newValue) {
      if (newValue) {
        this.startTimer();
      } else {
        this.clearTimers();
      }
    },
    timeout() {
      if (this.enabled) {
        this.clearTimers();
        this.startTimer();
      }
    }
  },
  methods: {
    startTimer() {
      this.remainingTime = this.timeout;

      // Configurar temporizador principal para recarregar a página
      this.timer = setTimeout(() => {
        window.location.reload();
      }, this.timeout);

      // Se o contador estiver ativado, atualize a cada segundo
      if (this.show) {
        this.countdownInterval = setInterval(() => {
          this.remainingTime -= 1000;
          if (this.remainingTime <= 0) {
            clearInterval(this.countdownInterval);
          }
        }, 1000);
      }
    },
    clearTimers() {
      if (this.timer) {
        clearTimeout(this.timer);
        this.timer = null;
      }

      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
      }
    }
  }
}
</script>

<style scoped>
.refresh-countdown {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px 15px;
  border-radius: 4px;
  font-size: 14px;
  z-index: 1000;
}
</style>
