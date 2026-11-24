<template>
  <div class="pcl-totalizacao px-2 py-1" v-if="resumo && resumo.itens">
    <div class="d-flex align-items-center justify-content-between mb-1 ">
      <div class="d-flex align-items-center">
        <i class="fas fa-chart-bar text-primary mr-2"></i>
        <strong class="text-dark">Totalização</strong>
      </div>
      <span class="small text-info ml-2 pl-2">
        <em>
          A Totalização é calculada sobre as emendas e ajustes listados conforme o filtro acima aplicado:
        </em>
        <strong class="total-registros">
          {{ resumo.itens }} {{ registros(resumo.itens) }}.
        </strong>
      </span>
    </div>

    <div class="d-flex align-items-stretch total-geral-row mb-2">
      <div
        v-for="g in grupos"
        :key="g.key"
        class="total-geral-box flex-fill d-flex flex-column px-3 py-2"
        :class="[`total-${g.key}`, { 'sub-total-box ml-2': g.key !== 'impositivas' }]"
      >
        <div class="d-flex">
          <i :class="[g.icon, `text-${g.variant}`, g.key === 'impositivas' ? 'mr-2' : 'mr-1']"></i>
          <span class="font-weight-bold" :class="g.key === 'impositivas' ? 'mr-2' : 'mr-1'">{{ g.label }}:</span>
        </div>
        <div class="d-flex flex-column align-items-center justify-content-center">
          <h2 class="font-weight-bold mb-0" :class="`text-${g.variant}`">R$ {{ formatCurrency(g.valor) }}</h2>
          <small class="text-muted">({{ g.quantidade }} {{ registros(g.quantidade) }})</small>
        </div>
      </div>
    </div>

    <div class="aviso-zeradas text-center mb-1" v-if="avisosZeradas.length">
      <small class="text-muted d-block" v-for="aviso in avisosZeradas" :key="aviso">
        <i class="fas fa-info-circle mr-1"></i>{{ aviso }}
      </small>
    </div>

    <div class="row mx-0 mb-1 linha-execucao" v-if="temExecucao && execucao.vale">
      <div
        v-for="(t, i) in totaisExecucao"
        :key="t.key"
        class="col-md-3 d-flex flex-column text-center py-1"
        :class="{ 'border-right': i < totaisExecucao.length - 1 }"
      >
        <span class="d-inline">
          <small class="text-muted">{{ t.label }}</small> <small class="text-muted text-blue">({{ percentual(t.valor).toFixed(2) }}%)</small>
        </span>
        <strong :class="`text-${t.variant}`">R$ {{ formatCurrency(t.valor) }}</strong>
      </div>
    </div>
    <div class="row mx-0 mb-1 aviso-execucao" v-else-if="temExecucao">
      <div class="col-md-12 text-center py-1">
        <small class="text-muted d-block">Totais de Empenho, Liquidação, Pagamento e Anulação computados apenas a partir da LOA {{ execucao.ano_inicial }}.</small>
      </div>
    </div>
  </div>
</template>

<script>
// Só apresenta: os números vêm prontos do backend (prestacaoconta_resumo,
// docs/specs/loa/prestacao-contas-consulta.md). Nenhuma regra de valor aqui.
export default {
  name: 'pcl-totalizacao',
  props: {
    resumo: { type: Object, default: null }
  },
  computed: {
    grupos () {
      const r = this.resumo
      const grupo = (key, label, icon, variant) => ({
        key,
        label,
        icon,
        variant,
        valor: Number(r[key].valor),
        quantidade: r[key].quantidade
      })
      const lista = [
        grupo('impositivas', 'Total Impositivas', 'fas fa-coins', 'success'),
        grupo('saude', 'Saúde', 'fas fa-heartbeat', 'success'),
        grupo('areas_diversas', 'Áreas Diversas', 'fas fa-th-large', 'info')
      ]
      const modificativas = grupo('modificativas', 'Modificativas', 'fas fa-pen-fancy', 'secondary')
      if (modificativas.valor > 0) lista.push(modificativas)
      return lista
    },
    execucao () {
      return this.resumo.execucao || {}
    },
    totaisExecucao () {
      const e = this.execucao
      return [
        { key: 'empenhado', label: 'Total Empenhado', variant: 'primary', valor: Number(e.empenhado || 0) },
        { key: 'liquidado', label: 'Total Liquidado', variant: 'info', valor: Number(e.liquidado || 0) },
        { key: 'pago_bruto', label: 'Total Pago', variant: 'success', valor: Number(e.pago_bruto || 0) },
        { key: 'anulado', label: 'Total Anulado', variant: 'danger', valor: Number(e.anulado || 0) }
      ]
    },
    temExecucao () {
      return this.totaisExecucao.some(t => t.valor > 0)
    },
    avisosZeradas () {
      const avisos = []
      const emAjuste = this.resumo.emendas_com_valor_em_ajuste
      if (emAjuste && emAjuste.quantidade) {
        const fora = this.resumo.ajustes ? '' : ', que não estão nesta seleção'
        avisos.push(
          `${emAjuste.quantidade} ${emAjuste.quantidade === 1 ? 'emenda conta' : 'emendas contam'} com valor zero ` +
          `(valor original de R$ ${this.formatCurrency(emAjuste.valor_original)}): ` +
          `o valor foi remanejado para registros de ajuste${fora}.`
        )
      }
      const impedidas = this.resumo.emendas_em_impedimento
      if (impedidas && impedidas.quantidade) {
        avisos.push(
          `${impedidas.quantidade} ${impedidas.quantidade === 1 ? 'emenda em impedimento técnico conta' : 'emendas em impedimento técnico contam'} ` +
          `com valor zero (valor original de R$ ${this.formatCurrency(impedidas.valor_original)}).`
        )
      }
      return avisos
    }
  },
  methods: {
    registros (quantidade) {
      return quantidade === 1 ? 'registro' : 'registros'
    },
    formatCurrency (value) {
      return Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    percentual (valor) {
      const total = Number(this.resumo.impositivas.valor || 0)
      return total ? (valor / total) * 100 : 0
    }
  }
}
</script>

<style scoped lang="scss">
.pcl-totalizacao {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
}
.total-geral-box {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  font-size: 0.95rem;
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
}
</style>
