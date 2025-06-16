<template>
  <div class="loa-dashboard">
    <h3>{{ title }}</h3>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useMessageStore } from '~@/js/stores/MessageStore'

// Injected dependency
const bus = inject('EventBus')

const title = ref('DASHBOARD')
const messageStore = useMessageStore()

// Constantes Locais
const observer = {
  apps: [ 'materia'],
  models: [ 'materialegislativa'],
}

// Methods

// Lifecycle hook
onMounted(() => {
  bus.on('time-refresh', (message) => {
    if (observer.apps.includes(message.app) && observer.models.includes(message.model)) {
      messageStore.addMessage({
        type: 'info',
        title: 'Time Refresh! ',
        text: `time-refresh ${message.id}  ${message.app} ${message.model}`,
        timeout: 5000
      })
    }
  })
})
</script>

<style lang="scss" scoped>
.loa-dashboard {
  min-height: 100vh;
  padding: 0 0.5rem;
  &::before {
    content: '';
    position: absolute;
    top: 5rem;
    left: 1rem;
    right: 1rem;
    bottom: 5rem;
    background: url('/imgs/brasao/brasao_1024.png') no-repeat center center;
    background-size: contain;
    opacity: 0.3;
  }
}
</style>
