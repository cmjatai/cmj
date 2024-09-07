<template>
  <div>
    <resize-observer @notify="handleResize" />
    <DoughnutChart v-if="chartData" :height="height" :chartDataUser="chartData"/>
  </div>
</template>

<script>
import DoughnutChart from '@/components/charts/DoughnutChart'

export default {
  name: 'LoaDetail',
  components: { DoughnutChart },
  data () {
    return {
      chartData: null,
      height: 600
    }
  },
  methods: {
    handleResize () {
      this.height = window.innerHeight * 0.7
    }
  },
  mounted: function () {
    this.chartData = {
      labels: ['VueJs', 'EmberJs', 'ReactJs', 'AngularJs'],
      datasets: [
        {
          backgroundColor: ['#41B883', '#E46651', '#00D8FF', '#DD1B16'],
          data: [40, 20, 80, 10]
        }
      ]
    }
  }
}
</script>
