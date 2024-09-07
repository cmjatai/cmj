<template>
  <div>
    <BarChart />
    <DoughnutChart />
  </div>
</template>

<script>
import BarChart from './BarChart'
import DoughnutChart from './DoughnutChart'

export default {
  name: 'LoaDetail',
  components: { BarChart, DoughnutChart }
}
</script>
