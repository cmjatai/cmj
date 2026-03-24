<template>
  <div class="pcl-totalizacao px-2 py-1" v-if="lista.length">
    <div class="d-flex align-items-center justify-content-between mb-1 ">
      <div class="d-flex align-items-center">
        <i class="fas fa-chart-bar text-primary mr-2"></i>
        <strong class="text-dark">Totalização</strong>
      </div>
      <span class="small text-info ml-2 pl-2 border-left border-info">
        <em>
          A Totalização é calculada sobre as emendas e ajustes listados conforme o filtro acima aplicado:
        </em>
        <strong>
          {{ lista.length }} {{ lista.length === 1 ? 'registro' : 'registros' }}.
        </strong>
      </span>
    </div>

    <div class="d-flex align-items-stretch total-geral-row mb-2">
      <div class="total-geral-box flex-fill d-flex align-items-center justify-content-center px-3 py-2">
        <i class="fas fa-coins text-success mr-2"></i>
        <span class="font-weight-bold mr-2">Total Geral:</span>
        <span class="font-weight-bold text-success">R$ {{ formatCurrency(totalGeral) }}</span>
      </div>
      <div class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ml-2">
        <i class="fas fa-heartbeat text-success mr-1"></i>
        <span class="font-weight-bold mr-1">Saúde:</span>
        <span class="font-weight-bold text-success">R$ {{ formatCurrency(totalSaude) }}</span>
      </div>
      <div class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ml-2">
        <i class="fas fa-th-large text-info mr-1"></i>
        <span class="font-weight-bold mr-1">Áreas Diversas:</span>
        <span class="font-weight-bold text-info">R$ {{ formatCurrency(totalAreasDiversas) }}</span>
      </div>
      <div v-if="totalModificativas > 0" class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ml-2">
        <i class="fas fa-pen-fancy text-secondary mr-1"></i>
        <span class="font-weight-bold mr-1">Modificativas:</span>
        <span class="font-weight-bold text-secondary">R$ {{ formatCurrency(totalModificativas) }}</span>
      </div>
    </div>

    <div class="grupos-row d-flex flex-wrap justify-content-center">
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
    lista: { type: Array, default: () => [] },
    parlamentarSelecionado: { type: Object, default: null }
  },
  computed: {
    totalGeral () {
      return this.lista.reduce((sum, item) => {
        return sum + Number(this.valorEfetivo(item))
      }, 0)
    },
    totalSaude () {
      return this.lista
        .filter(item => item.tipo === 10)
        .reduce((sum, item) => sum + Number(this.valorEfetivo(item)), 0)
    },
    totalAreasDiversas () {
      return this.lista
        .filter(item => item.tipo === 99)
        .reduce((sum, item) => sum + Number(this.valorEfetivo(item)), 0)
    },
    totalModificativas () {
      return this.lista
        .filter(item => item.tipo === 0)
        .reduce((sum, item) => sum + Number(this.valorEfetivo(item)), 0)
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
        return item.valor || 0
      }
      const valor_computado = Number(item.valor_computado || 0)
      if (item.has_ajustes || item.fase === 40) {
        return valor_computado
      }

      let valor_inicial = Number(item.valor_inicial || 0)
      if (this.parlamentarSelecionado && item.valor_inicial_por_parlamentar) {
        const vid = item.valor_inicial_por_parlamentar[this.parlamentarSelecionado.id]
        if (vid !== undefined) {
          valor_inicial = Number(vid)
        }
      }
      return valor_inicial
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
  margin: 0 -15px;
}
.total-geral-box {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  font-size: 0.95rem;
}
.sub-total-box {
  font-size: 0.85rem;
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

/* ===== Responsivo < 992px ===== */
@media (max-width: 991.98px) {
  .grupos-row .grupo-box {
    flex: 1 1 auto;
  }
}

/* ===== Responsivo < 768px ===== */
@media (max-width: 767.98px) {
  .total-geral-row {
    flex-direction: column;
  }
  .total-geral-row .sub-total-box {
    margin-left: 0 !important;
    margin-top: 0.25rem;
  }
  .total-geral-box {
    font-size: 0.85rem;
  }
  .grupo-box {
    font-size: 0.75rem;
    white-space: normal;
  }
}

/* ===== Responsivo < 425px ===== */
@media (max-width: 425px) {
  .grupos-row {
    flex-direction: column;
  }
  .grupo-box {
    margin-right: 0 !important;
    width: 100%;
  }
}
</style>
