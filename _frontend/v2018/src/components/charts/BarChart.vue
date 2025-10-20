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
    }
  },
  data () {
    return {
      chartData: null,
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'teste'
          },
          legend: {
            position: 'bottom',
            onClick: this.handleClick,
            labels: {
              font: {
                family: "'Courier New', Courier, monospace",
                size: 15
              }
            }
          },
          datalabels: {
            formatter: (value, ctx) => {
              let dataset = ctx.dataset.data
              let sum = 0
              dataset.map(ds => {
                sum += ds
              })
              let percentage = ((value / sum) * 100).toFixed(0) + '%'
              return percentage
            },
            color: '#0000',
            rotation: -60,
            align: 'top'
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
    handleClick (evt, item, legend) {
      // console.debug(evt, item, legend)
    }
  },
  mounted: function () {
    this.chartOptions.plugins.title.text = this.plugins[0].title.text
    this.chartData = this.chartDataUser
  }
}
</script>
