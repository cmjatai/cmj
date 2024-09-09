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
    chartDataUser: {
      type: Object,
      default: () => {}
    },
    datasetIdKey: {
      type: String,
      default: 'label'
    },
    width: {
      type: Number,
      default: 1140
    },
    height: {
      type: Number,
      default: 500
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
    }
  },
  data () {
    return {
      chartData: null,
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: 15
        },
        plugins: {
          title: {
            display: true,
            text: '',
            padding: {
              top: -15,
              bottom: 20
            }
          },
          legend: {
            position: 'left',
            onHover: this.handleHover,
            onLeave: this.handleLeave,
            labels: {
              font: {
                family: "'Courier New', Courier, monospace",
                size: 15
              },
              padding: 2
            }
          },
          datalabels: {
            formatter: (value, ctx) => {
              let dataset = ctx.dataset.data
              let sum = 0
              dataset.map(ds => {
                sum += ds
              })
              let percentage = ((value / sum) * 100).toFixed(1) + '%'
              return percentage
            },
            color: '#fff'
          }
        }
      }
    }
  },
  watch: {
    plugins: function (nv, ov) {
      this.chartOptions.plugins.title.text = nv[0].title.text
    }
  },
  methods: {
    handleHover (evt, item, legend) {
      legend.chart.data.datasets[0].backgroundColor.forEach((color, index, colors) => {
        colors[index] = index === item.index || color.length === 9 ? color : color + '3d'
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
    this.chartOptions.plugins.title.text = this.plugins[0].title.text
    this.chartData = this.chartDataUser
  }
}
</script>
<style lang="scss">

</style>
