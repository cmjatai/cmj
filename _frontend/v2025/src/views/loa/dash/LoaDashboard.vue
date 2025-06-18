<template>
  <div class="loa-dashboard">
    <h3>{{ title }}</h3>
    <slot></slot>

    <div class="grid container-fluid" v-for="(rows, gidx) in grid" :key="`g0_${gidx}`">
      <div class="row" v-for="(row0, r0idx) in rows" :key="`r0_${r0idx}`">
        <div
          :class="`col-12 col-md-${col0[1]}`"
          v-for="(col0, c0idx) in row0.cols"
          :key="`c0_${c0idx}`"
        >
          <template v-if="_.isObject(col0[0])">
            <div class="row" v-for="(row1, r1idx) in col0[0].rows" :key="`r1_${r1idx}`">
              <div
                :class="`col-12 col-md-${col1[1]}`"
                v-for="(col1, c1idx) in row1.cols"
                :key="`c1_${c1idx}`"
              >
                {{ col1[0] }} - {{ col1[1] }} - {{ col0[1] }}
              </div>
            </div>
          </template>
          <template v-else>
            {{ col0[0] }} - {{ col0[1] }}
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useMessageStore } from '~@/js/stores/MessageStore'
import _ from 'lodash'

// Injected dependency
const bus = inject('EventBus')

const title = ref('DASHBOARD')
const messageStore = useMessageStore()

// Constantes Locais
const observer = {
  apps: [ 'materia'],
  models: [ 'materialegislativa'],
}

const grid = ref(null)

fetch('?grid')
  .then(response => response.json())
  .then(data => {
    console.log('Grid data:', data)
    grid.value = data
  })
  .catch(error => {
    console.error('Error fetching grid data:', error)
  })

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
