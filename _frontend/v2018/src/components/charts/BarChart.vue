<template>
  <Bar v-if="chartData"
    :chart-options="chartOptions"
    :chart-data="chartData"
    :chart-id="chartId"
    :dataset-id-key="datasetIdKey"
    :plugins="plugins"
    :css-classes="cssClasses"
    :styles="styles"
    :width="width"
    :height="height"
  />
</template>

<script>
import { Bar } from 'vue-chartjs/legacy'
import ChartDataLabels from 'chartjs-plugin-datalabels'

import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, ChartDataLabels, BarElement, CategoryScale, LinearScale)

export default {
  name: 'BarChart',
  components: {
    Bar
  },
  props: {
    chartId: {
      type: String,
      default: 'bar-chart'
    },
    chartDataUser: {
      type: Object,
      default: () => {}
    },
    datasetIdKey: {
      type: String,
      default: 'label1'
    },
    width: {
      type: Number,
      default: 1140
    },
    height: {
      type: Number,
      default: 600
    },
    cssClasses: {
      default: '',
      type: String
    },
    styles: {
      type: Object,
      default: () => {}
    },
    plugins: {
      type: Array,
      default: () => []
    },
    horizontal: {
      type: Boolean,
      default: false
    },
    valueFormatter: {
      type: Function,
      default: (value) => value
    }
  },
  data () {
    return {
      chartData: null
    }
  },
  computed: {
    chartOptions () {
      const t = this
      const base = {
        indexAxis: this.horizontal ? 'y' : 'x',
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: this.horizontal ? { right: 48 } : { top: 24 }
        },
        plugins: {
          title: {
            display: true,
            text: (this.plugins[0] && this.plugins[0].title && this.plugins[0].title.text) || ''
          },
          legend: {
            display: !this.horizontal,
            position: 'bottom',
            onClick: this.handleClick,
            labels: {
              font: {
                family: "'Courier New', Courier, monospace",
                size: 15
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label ? ctx.dataset.label + ': ' : ''}${t.valueFormatter(ctx.parsed[t.horizontal ? 'x' : 'y'])}`
            }
          },
          datalabels: this.horizontal
            ? {
              formatter: (value) => t.valueFormatter(value),
              color: '#495057',
              anchor: 'end',
              align: 'end',
              offset: 4,
              font: { size: 12, weight: 'bold' }
            }
            : {
              formatter: (value, ctx) => {
                const dataset = ctx.dataset.data
                const sum = dataset.reduce((acc, v) => acc + v, 0)
                return sum ? ((value / sum) * 100).toFixed(0) + '%' : ''
              },
              color: '#0000',
              rotation: -60,
              align: 'top'
            }
        }
      }

      if (this.horizontal) {
        base.scales = {
          x: {
            beginAtZero: true,
            grid: { color: '#e9ecef' },
            ticks: { callback: (value) => t.valueFormatter(value) }
          },
          y: {
            grid: { display: false },
            ticks: { font: { size: 13 } }
          }
        }
      }

      return base
    }
  },
  watch: {
    chartDataUser: {
      immediate: true,
      handler (nv) {
        this.chartData = nv
      }
    }
  },
  methods: {
    handleClick (evt, item, legend) {
      // console.debug(evt, item, legend)
    }
  }
}
</script>
