<template>
  <div>
    <DoughnutChart v-if="chartData" :height="800" :chartDataUser="chartData"/>
  </div>
</template>

<script>
import DoughnutChart from './DoughnutChart'

export default {
  name: 'LoaDetail',
  components: { DoughnutChart },
  data () {
    return {
      chartData: null
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
