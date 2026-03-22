<template>
  <div class="pcl-totalizacao" v-if="lista.length">
    <div class="d-flex align-items-center justify-content-between mb-2">
      <div class="d-flex align-items-center">
        <i class="fas fa-chart-bar text-primary mr-2"></i>
        <strong class="text-dark">Totalização</strong>
      </div>
      <span class="text-muted small">
        {{ lista.length }} {{ lista.length === 1 ? 'registro' : 'registros' }}
      </span>
    </div>

    <div class="d-flex align-items-stretch total-geral-row mb-2">
      <div class="total-geral-box flex-fill d-flex align-items-center px-3 py-2">
        <i class="fas fa-coins text-success mr-2"></i>
        <span class="font-weight-bold mr-2">Total Geral:</span>
        <span class="font-weight-bold text-success">R$ {{ formatCurrency(totalGeral) }}</span>
      </div>
    </div>

    <div class="grupos-row d-flex flex-wrap">
      <div
        v-for="g in grupos"
        :key="g.key"
        class="grupo-box d-flex align-items-center mr-2 mb-1 px-2 py-1"
        :class="`border-${g.variant}`"
      >
        <i :class="[g.icon, `text-${g.variant}`]" class="mr-1"></i>
        <span class="grupo-label mr-1">{{ g.label }}</span>
        <b-badge :variant="g.variant" pill class="mr-1">{{ g.count }}</b-badge>
        <span class="grupo-valor font-weight-bold">R$ {{ formatCurrency(g.total) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { isEmenda, tipoLabel, tipoVariant } from './utils/pcl-helpers'

const TIPO_ICONS = {
  0: 'fas fa-pen-fancy',
  10: 'fas fa-heartbeat',
  99: 'fas fa-th-large'
}

export default {
  name: 'pcl-totalizacao',
  props: {
    lista: { type: Array, default: () => [] }
  },
  computed: {
    totalGeral () {
      return this.lista.reduce((sum, item) => {
        return sum + Number(this.valorEfetivo(item))
      }, 0)
    },
    grupos () {
      const map = {}
      this.lista.forEach(item => {
        const emenda = isEmenda(item)
        const tipo = item.tipo
        const prefix = emenda ? 'emenda' : 'ajuste'
        const key = `${prefix}_${tipo}`

        if (!map[key]) {
          const label = emenda
            ? tipoLabel(tipo)
            : `Ajuste ${tipo === 10 ? 'Saúde' : 'Áreas Diversas'}`
          map[key] = {
            key,
            label,
            variant: emenda ? tipoVariant(tipo) : 'warning',
            icon: emenda ? (TIPO_ICONS[tipo] || 'fas fa-file-alt') : 'fas fa-exchange-alt',
            count: 0,
            total: 0,
            order: emenda ? tipo : 1000 + tipo
          }
        }
        map[key].count++
        map[key].total += Number(this.valorEfetivo(item))
      })
      return Object.values(map).sort((a, b) => a.order - b.order)
    }
  },
  methods: {
    valorEfetivo (item) {
      if (!isEmenda(item)) {
        if (!item.emendaloa || item.emendaloa.length === 0) {
          return item.valor || 0
        }
        return 0
        /* const emendasValorInicial = item.emendaloa.reduce((sum, em) => {
          return sum + Number(em.valor_inicial || 0)
        }, 0)
        const valor = emendasValorInicial - Number(item.valor || 0)
        return valor */
      }
      const computado = Number(item.valor_computado || 0)
      const inicial = Number(item.valor_inicial || 0)
      // return computado
      return computado !== inicial ? computado - inicial : computado
    },
    formatCurrency (value) {
      return Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }
  }
}
</script>

<style scoped lang="scss">
.pcl-totalizacao {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
}
.total-geral-box {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  font-size: 0.95rem;
}
.grupo-box {
  background: #fff;
  border: 1px solid;
  border-radius: 0.25rem;
  font-size: 0.82rem;
  white-space: nowrap;
}
.grupo-label {
  color: #495057;
}
.grupo-valor {
  color: #212529;
}
</style>
