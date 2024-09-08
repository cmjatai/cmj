<template>
  <Doughnut v-if="chartData"
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
import { Doughnut } from 'vue-chartjs/legacy'
import ChartDataLabels from 'chartjs-plugin-datalabels'

import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, ChartDataLabels, ArcElement, CategoryScale)

export default {
  name: 'DoughnutChart',
  components: {
    Doughnut
  },
  props: {
    chartId: {
      type: String,
      default: 'doughnut-chart'
    },
    datasetIdKey: {
      type: String,
      default: 'label'
    },
    width: {
      type: Number,
      default: 1000
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
    chartDataUser: {
      type: Object,
      default: () => {}
    }
  },
  data () {
    return {
      chartData: null,
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            onHover: this.handleHover,
            onLeave: this.handleLeave
          },
          datalabels: {
            formatter: (value, ctx) => {
              let dataset = ctx.dataset.data
              let sum = 0
              dataset.map(ds => {
                sum += ds
              })
              let percentage = ((value / sum) * 100).toFixed(2) + '%'
              return percentage
            },
            color: '#fff'
          }
        }
      }
    }
  },
  methods: {
    handleHover (evt, item, legend) {
      legend.chart.data.datasets[0].backgroundColor.forEach((color, index, colors) => {
        colors[index] = index === item.index || color.length === 9 ? color : color + '77'
      })
      legend.chart.update()
    },
    handleLeave (evt, item, legend) {
      legend.chart.data.datasets[0].backgroundColor.forEach((color, index, colors) => {
        colors[index] = color.length === 9 ? color.slice(0, -2) : color
      })
      legend.chart.update()
    }
  },
  mounted: function () {
    this.chartData = this.chartDataUser
  }
}
</script>
<style lang="scss">

</style>
