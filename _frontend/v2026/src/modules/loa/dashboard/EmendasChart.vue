<template>
  <div class="emenda-chart card mb-3">
    <div class="card-body">
      <h5
        v-if="title"
        class="card-title"
      >
        {{ title }}
      </h5>
      <p
        v-if="subtitle"
        class="card-subtitle text-muted"
      >
        {{ subtitle }}
      </p>
      <div
        class="emendas-chart-area"
        :style="{ height: chartHeight }"
      >
        <Bar
          v-if="chartData"
          :data="chartData"
          :options="chartOptions"
        />
        <div
          v-else
          class="text-center text-body-secondary py-4"
        >
          <FontAwesomeIcon
            icon="chart-bar"
            class="me-2"
          />
          Nenhuma emenda encontrada
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  emendas: {
    type: Array,
    default: () => []
  },
  barHeight: {
    type: Number,
    default: 24
  },
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const isDark = ref(document.documentElement.getAttribute('data-bs-theme') === 'dark')
let observer = null

onMounted(() => {
  observer = new MutationObserver(() => {
    isDark.value = document.documentElement.getAttribute('data-bs-theme') === 'dark'
  })
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] })
})

onUnmounted(() => {
  observer?.disconnect()
})

const agrupado = computed(() => {
  const map = {}
  for (const emenda of props.emendas) {
    const label = emenda.indicacao || 'Sem Registro de Indicação'
    if (!map[label]) map[label] = 0
    map[label] += Number(emenda.valor)
  }
  const entries = Object.entries(map).sort((a, b) => b[1] - a[1])
  return {
    labels: entries.map(([label]) => label),
    values: entries.map(([, val]) => val)
  }
})

const PALETTE_DARK = [
  { bg: 'rgba(13, 110, 253, 0.7)', border: 'rgba(13, 110, 253, 1)' },
  { bg: 'rgba(25, 135, 84, 0.7)', border: 'rgba(25, 135, 84, 1)' },
  { bg: 'rgba(220, 53, 69, 0.7)', border: 'rgba(220, 53, 69, 1)' },
  { bg: 'rgba(255, 193, 7, 0.75)', border: 'rgba(255, 193, 7, 1)' },
  { bg: 'rgba(13, 202, 240, 0.7)', border: 'rgba(13, 202, 240, 1)' },
  { bg: 'rgba(111, 66, 193, 0.7)', border: 'rgba(111, 66, 193, 1)' },
  { bg: 'rgba(253, 126, 20, 0.7)', border: 'rgba(253, 126, 20, 1)' },
  { bg: 'rgba(102, 16, 242, 0.7)', border: 'rgba(102, 16, 242, 1)' },
  { bg: 'rgba(214, 51, 132, 0.7)', border: 'rgba(214, 51, 132, 1)' },
  { bg: 'rgba(32, 201, 151, 0.7)', border: 'rgba(32, 201, 151, 1)' }
]

const PALETTE_LIGHT = [
  { bg: 'rgba(13, 110, 253, 0.7)', border: 'rgba(13, 110, 253, 1)' },
  { bg: 'rgba(25, 135, 84, 0.7)', border: 'rgba(25, 135, 84, 1)' },
  { bg: 'rgba(200, 35, 51, 0.7)', border: 'rgba(200, 35, 51, 1)' },
  { bg: 'rgba(204, 153, 0, 0.7)', border: 'rgba(204, 153, 0, 1)' },
  { bg: 'rgba(10, 160, 190, 0.7)', border: 'rgba(10, 160, 190, 1)' },
  { bg: 'rgba(90, 50, 170, 0.7)', border: 'rgba(90, 50, 170, 1)' },
  { bg: 'rgba(220, 100, 10, 0.7)', border: 'rgba(220, 100, 10, 1)' },
  { bg: 'rgba(80, 10, 200, 0.7)', border: 'rgba(80, 10, 200, 1)' },
  { bg: 'rgba(185, 40, 110, 0.7)', border: 'rgba(185, 40, 110, 1)' },
  { bg: 'rgba(20, 170, 130, 0.7)', border: 'rgba(20, 170, 130, 1)' }
]

const chartHeight = computed(() => {
  const count = agrupado.value.labels.length
  if (!count) return '100px'
  const padding = 60
  return `${count * props.barHeight + padding}px`
})

const chartData = computed(() => {
  if (!agrupado.value.labels.length) return null
  const count = agrupado.value.values.length
  const palette = isDark.value ? PALETTE_DARK : PALETTE_LIGHT
  return {
    labels: agrupado.value.labels,
    datasets: [
      {
        label: 'Valor (R$)',
        data: agrupado.value.values,
        backgroundColor: Array.from({ length: count }, (_, i) => palette[i % palette.length].bg),
        borderColor: Array.from({ length: count }, (_, i) => palette[i % palette.length].border),
        borderWidth: 1,
        borderRadius: 4,
        barThickness: props.barHeight * 0.9,
        minBarLength: 5
      }
    ]
  }
})

const chartOptions = computed(() => {
  const dark = isDark.value
  const textColor = dark ? '#adb5bd' : '#495057'
  const gridColor = dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'

  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (ctx) =>
            Number(ctx.raw).toLocaleString('pt-BR', {
              style: 'currency',
              currency: 'BRL'
            })
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: textColor,
          callback: (val) =>
            Number(val).toLocaleString('pt-BR', {
              style: 'currency',
              currency: 'BRL',
              maximumFractionDigits: 0
            })
        },
        grid: {
          color: gridColor
        }
      },
      y: {
        ticks: {
          color: textColor
        },
        grid: {
          display: false
        }
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.emenda-chart {
  width: 100%;
  background-color: var(--cmj-chart-bg);
}
</style>
