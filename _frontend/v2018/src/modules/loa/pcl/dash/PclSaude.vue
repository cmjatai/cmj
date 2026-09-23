<template>
  <div class="pcl-saude">
    <BarChart v-if="chartData" :plugins="pluginsBar" :chartDataUser="chartData" :horizontal="true" cssClasses="barchart-component"/>
    </div>
</template>

<script>

import BarChart from '@/components/charts/BarChart'

export default {
  name: 'pcl-saude',
  components: {
    BarChart
  },
  props: {
    lista: { type: Array, default: () => [] },
    parlamentarSelecionado: { type: Object, default: null },
    loasChoice: { type: Array, default: () => [] },
    selectedLoaIds: { type: Array, default: () => [] },
    totaisEmpenhos: { type: Object, default: () => ({}) }
  },
  data () {
    return {
      pluginsBar: [{
        title: {
          display: true,
          text: ''
        }
      }]
    }
  },
  computed: {
    chartData () {
      if (!this.lista.length) return null
      // os labels vem da propriedade 'entidade.nome_fantasia' de cada item da lista
      // itens com o mesmo 'entidade.nome_fantasia' devem ser agregados
      // entidade pode ser nula ou indefinida, neste caso deve ser criar um label genérico como 'Indefinido'
      return {
        labels: [...new Set(this.lista.map(item => item.entidade?.nome_fantasia || 'Indefinido'))],
        datasets: [
          {
            data: [...new Set(this.lista.map(item => item.entidade?.nome_fantasia || 'Indefinido'))].map(label =>
              this.lista
                .filter(item => (item.entidade?.nome_fantasia || 'Indefinido') === label)
                .reduce((sum, item) => sum + item.valor_computado, 0)
            ),
            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
          }
        ]
      }
    }
  }
}
</script>
<style lang="scss">
</style>
