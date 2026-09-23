<template>
  <div class="pcl-saude">
    <BarChart
      v-if="chartData"
      :plugins="pluginsBar"
      :chart-data-user="chartData"
      :horizontal="true"
      :height="chartHeight"
      :value-formatter="formatCurrency"
      css-classes="barchart-component"
    />
  </div>
</template>

<script>

import BarChart from '@/components/charts/BarChart'
import { isEmenda } from '../utils/pcl-helpers'

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
          text: 'Totalização por Entidade de Saúde'
        }
      }]
    }
  },
  computed: {
    entidadesAgrupadas () {
      // agrega os valores por 'entidade.nome_fantasia', tratando entidade nula/indefinida
      const totais = new Map()
      this.lista.forEach(item => {
        const label = item.entidade?.nome_fantasia || 'Indefinido'
        totais.set(label, (totais.get(label) || 0) + this.valorEfetivo(item))
      })
      // remove entidades com valor total zerado e ordena do maior para o menor valor
      return [...totais.entries()].filter(([, valor]) => valor !== 0).sort((a, b) => b[1] - a[1])
    },
    chartData () {
      if (!this.entidadesAgrupadas.length) return null
      return {
        labels: this.entidadesAgrupadas.map(([label]) => label),
        datasets: [
          {
            data: this.entidadesAgrupadas.map(([, valor]) => valor),
            backgroundColor: this.buildColors(this.entidadesAgrupadas.length),
            borderRadius: 4,
            maxBarThickness: 32
          }
        ]
      }
    },
    chartHeight () {
      // altura proporcional à quantidade de barras, evitando labels espremidos
      return Math.max(300, this.entidadesAgrupadas.length * 48 + 80)
    }
  },
  methods: {
    valorEfetivo (item) {
      if (!isEmenda(item)) {
        let valor = Number(item.valor || 0)
        if (this.parlamentarSelecionado && item.valor_por_parlamentar) {
          const vp = item.valor_por_parlamentar[this.parlamentarSelecionado.id]
          if (vp !== undefined) valor = Number(vp)
        }
        return valor
      }
      const valorComputado = Number(item.valor_computado || 0)
      if (item.has_ajustes || item.fase === 40) return valorComputado

      let valorInicial = Number(item.valor_inicial || 0)
      if (this.parlamentarSelecionado && item.valor_inicial_por_parlamentar) {
        const vid = item.valor_inicial_por_parlamentar[this.parlamentarSelecionado.id]
        if (vid !== undefined) valorInicial = Number(vid)
      }
      return valorInicial
    },
    buildColors (n) {
      const colors = []
      let hue = 200
      for (let i = 0; i < n; i++) {
        colors.push(`hsl(${hue}, 65%, 50%)`)
        hue = (hue + 47) % 360
      }
      return colors
    },
    formatCurrency (value) {
      return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)
    }
  }
}
</script>
<style lang="scss">
.pcl-saude {
  .barchart-component {
    background-color: #fff;
    border-radius: .5rem;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, .08);
  }
}
</style>
