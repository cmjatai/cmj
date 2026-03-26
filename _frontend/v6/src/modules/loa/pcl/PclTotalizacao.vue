<template>
  <div
    class="pcl-totalizacao px-2 py-1"
    v-if="lista.length"
  >
    <div class="d-flex align-items-center justify-content-between mb-1">
      <div class="d-flex align-items-center">
        <FontAwesomeIcon
          icon="chart-bar"
          class="text-primary me-2"
        />
        <strong class="text-body">Totalização</strong>
      </div>
      <span class="small text-info ms-2 ps-2">
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
        <FontAwesomeIcon
          icon="coins"
          class="text-success me-2"
        />
        <span class="fw-bold me-2">Total Impositivas:</span>
        <span class="fw-bold text-success">R$ {{ formatCurrency(totalGeral) }}</span>
      </div>
      <div class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ms-2">
        <FontAwesomeIcon
          icon="heartbeat"
          class="text-success me-1"
        />
        <span class="fw-bold me-1">Saúde:</span>
        <span class="fw-bold text-success">R$ {{ formatCurrency(totalSaude) }}</span>
      </div>
      <div class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ms-2">
        <FontAwesomeIcon
          icon="th-large"
          class="text-info me-1"
        />
        <span class="fw-bold me-1">Áreas Diversas:</span>
        <span class="fw-bold text-info">R$ {{ formatCurrency(totalAreasDiversas) }}</span>
      </div>
      <div
        v-if="totalModificativas > 0"
        class="total-geral-box sub-total-box flex-fill d-flex align-items-center justify-content-center px-3 py-2 ms-2"
      >
        <FontAwesomeIcon
          icon="pen-fancy"
          class="text-secondary me-1"
        />
        <span class="fw-bold me-1">Modificativas:</span>
        <span class="fw-bold text-secondary">R$ {{ formatCurrency(totalModificativas) }}</span>
      </div>
    </div>

    <div class="grupos-row d-flex flex-wrap justify-content-center">
      <div
        v-for="g in grupos"
        :key="g.key"
        class="grupo-box d-flex align-items-center me-2 mb-1 px-2 py-1"
        :class="`border-${g.variant}`"
      >
        <FontAwesomeIcon
          :icon="g.faIcon"
          :class="`text-${g.variant} me-1`"
        />
        <span class="grupo-label me-1">{{ g.label }}</span>
        <span :class="['badge', 'rounded-pill', `text-bg-${g.variant}`, 'me-1']">{{ g.count }}</span>
        <span class="grupo-valor fw-bold">R$ {{ formatCurrency(g.total) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { isEmenda, tipoLabel, tipoVariant, formatCurrency } from './utils/pcl-helpers'

const TIPO_ICONS = {
  0: 'pen-fancy',
  10: 'heartbeat',
  99: 'th-large'
}

const props = defineProps({
  lista: { type: Array, default: () => [] },
  parlamentarSelecionado: { type: Object, default: null }
})

function valorEfetivo (item) {
  if (!isEmenda(item)) {
    let valor = Number(item.valor || 0)
    if (props.parlamentarSelecionado && item.valor_por_parlamentar) {
      const vp = item.valor_por_parlamentar[props.parlamentarSelecionado.id]
      if (vp !== undefined) valor = Number(vp)
    }
    return valor
  }
  const valor_computado = Number(item.valor_computado || 0)
  if (item.has_ajustes || item.fase === 40) return valor_computado

  let valor_inicial = Number(item.valor_inicial || 0)
  if (props.parlamentarSelecionado && item.valor_inicial_por_parlamentar) {
    const vid = item.valor_inicial_por_parlamentar[props.parlamentarSelecionado.id]
    if (vid !== undefined) valor_inicial = Number(vid)
  }
  return valor_inicial
}

const totalGeral = computed(() =>
  props.lista
    .filter(item => item.tipo !== 0)
    .reduce((sum, item) => sum + Number(valorEfetivo(item)), 0)
)

const totalSaude = computed(() =>
  props.lista
    .filter(item => item.tipo === 10)
    .reduce((sum, item) => sum + Number(valorEfetivo(item)), 0)
)

const totalAreasDiversas = computed(() =>
  props.lista
    .filter(item => item.tipo === 99)
    .reduce((sum, item) => sum + Number(valorEfetivo(item)), 0)
)

const totalModificativas = computed(() =>
  props.lista
    .filter(item => item.tipo === 0)
    .reduce((sum, item) => sum + Number(valorEfetivo(item)), 0)
)

const grupos = computed(() => {
  const map = {}
  props.lista.forEach(item => {
    const emenda = isEmenda(item)
    const tipo = item.tipo
    if (tipo === 0) return

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
        faIcon: emenda ? (TIPO_ICONS[tipo] || 'file-alt') : 'exchange-alt',
        count: 0,
        total: 0,
        order: emenda && tipo !== 0 ? tipo : (!emenda ? 1000 + tipo : 10000)
      }
    }
    map[key].count++
    map[key].total += Number(valorEfetivo(item))
  })
  return Object.values(map).sort((a, b) => a.order - b.order)
})
</script>

<style scoped lang="scss">
.pcl-totalizacao {
  background: var(--bs-tertiary-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.375rem;
}

.total-geral-box {
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.25rem;
  font-size: 0.95rem;
}

.sub-total-box {
  font-size: 0.85rem;
}

.grupo-box {
  background: var(--bs-body-bg);
  border: 1px solid;
  border-radius: 0.25rem;
  font-size: 0.82rem;
  white-space: nowrap;
}

.grupo-label {
  color: var(--bs-secondary-color);
}

.grupo-valor {
  color: var(--bs-body-color);
}

@media (max-width: 991.98px) {
  .grupos-row .grupo-box {
    flex: 1 1 auto;
  }
}

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
