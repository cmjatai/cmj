<template>
  <div class="pcl-dashboard" v-if="lista.length">

    <!-- ===== SEÇÃO 1: KPIs ===== -->
    <div class="dash-section">
      <div class="dash-section-title">
        <i class="fas fa-coins mr-2"></i>Resumo por Tipo
      </div>
      <div class="d-flex flex-wrap dash-kpi-row">
        <div class="dash-kpi-card flex-fill">
          <div class="dash-kpi-icon text-success"><i class="fas fa-coins"></i></div>
          <div class="dash-kpi-body">
            <div class="dash-kpi-label">Total Impositivas</div>
            <div class="dash-kpi-value text-success">R$ {{ formatCurrency(kpis.totalImpositivas) }}</div>
            <small class="text-muted">{{ kpis.countImpositivas }} registro{{ kpis.countImpositivas !== 1 ? 's' : '' }}</small>
          </div>
        </div>
        <div class="dash-kpi-card flex-fill">
          <div class="dash-kpi-icon text-success"><i class="fas fa-heartbeat"></i></div>
          <div class="dash-kpi-body">
            <div class="dash-kpi-label">Saúde</div>
            <div class="dash-kpi-value text-success">R$ {{ formatCurrency(kpis.totalSaude) }}</div>
            <small class="text-muted">{{ kpis.countSaude }} registro{{ kpis.countSaude !== 1 ? 's' : '' }}</small>
          </div>
        </div>
        <div class="dash-kpi-card flex-fill">
          <div class="dash-kpi-icon text-info"><i class="fas fa-th-large"></i></div>
          <div class="dash-kpi-body">
            <div class="dash-kpi-label">Áreas Diversas</div>
            <div class="dash-kpi-value text-info">R$ {{ formatCurrency(kpis.totalAreasDiversas) }}</div>
            <small class="text-muted">{{ kpis.countAreasDiversas }} registro{{ kpis.countAreasDiversas !== 1 ? 's' : '' }}</small>
          </div>
        </div>
        <div v-if="kpis.countModificativas > 0" class="dash-kpi-card flex-fill">
          <div class="dash-kpi-icon text-secondary"><i class="fas fa-pen-fancy"></i></div>
          <div class="dash-kpi-body">
            <div class="dash-kpi-label">Modificativas</div>
            <div class="dash-kpi-value text-secondary">R$ {{ formatCurrency(kpis.totalModificativas) }}</div>
            <small class="text-muted">{{ kpis.countModificativas }} registro{{ kpis.countModificativas !== 1 ? 's' : '' }}</small>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 2: Distribuição por Situação/Fase ===== -->
    <div class="dash-section" v-if="faseDistribuicao.length">
      <div class="dash-section-title">
        <i class="fas fa-tasks mr-2"></i>Distribuição por Situação
      </div>
      <div class="dash-progress-container">
        <div class="progress dash-progress-bar">
          <div
            v-for="f in faseDistribuicao"
            :key="f.key"
            class="progress-bar"
            :style="{ width: f.pct + '%', backgroundColor: f.color }"
            :title="`${f.label} (${f.tipoLabel}): ${f.count} (${f.pct.toFixed(1)}%)`"
          ></div>
        </div>
        <div class="dash-legend d-flex flex-wrap mt-2">
          <div v-for="f in faseDistribuicao" :key="'leg_' + f.key" class="dash-legend-item mr-3 mb-1">
            <span class="dash-legend-dot" :style="{ backgroundColor: f.color }"></span>
            <span class="dash-legend-label">{{ f.label }}</span>
            <span class="badge badge-light ml-1" style="font-size:.7rem">{{ f.tipoLabel }}</span>
            <strong class="ml-1">{{ f.count }}</strong>
            <span class="text-muted ml-1">(R$ {{ formatCurrency(f.total) }})</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 3: Distribuição por Parlamentar ===== -->
    <div class="dash-section" v-if="parlamentarDistribuicao.length">
      <div class="dash-section-title">
        <i class="fas fa-users mr-2"></i>Distribuição por Parlamentar
      </div>
      <div class="dash-bar-list">
        <div
          v-for="p in parlamentarDistribuicao"
          :key="p.id"
          class="dash-bar-item d-flex align-items-center"
        >
          <img
            v-if="p.fotografia"
            :src="fotoThumb(p.fotografia)"
            :alt="p.nome"
            class="dash-bar-avatar mr-2"
          >
          <div v-else class="dash-bar-avatar-placeholder mr-2">
            <i class="fas fa-user"></i>
          </div>
          <div class="flex-grow-1 min-w-0">
            <div class="d-flex justify-content-between align-items-baseline mb-1">
              <span class="dash-bar-name text-truncate">{{ p.nome }}</span>
              <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">R$ {{ formatCurrency(p.total) }}</span>
            </div>
            <div class="progress dash-bar-progress">
              <div
                class="progress-bar bg-primary"
                :style="{ width: p.pct + '%' }"
              ></div>
            </div>
            <small class="text-muted">
              {{ p.emendas }} emenda{{ p.emendas !== 1 ? 's' : '' }},
              {{ p.ajustes }} ajuste{{ p.ajustes !== 1 ? 's' : '' }}
            </small>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 4: Distribuição por Unidade Orçamentária ===== -->
    <div class="dash-section" v-if="unidadeDistribuicao.length">
      <div class="dash-section-title">
        <i class="fas fa-building mr-2"></i>Distribuição por Unidade Orçamentária
        <small v-if="unidadeDistribuicaoExtra > 0" class="text-muted ml-2">
          (top {{ unidadeDistribuicao.length }} de {{ unidadeDistribuicao.length + unidadeDistribuicaoExtra }})
        </small>
      </div>
      <div class="dash-bar-list">
        <div
          v-for="u in unidadeDistribuicao"
          :key="u.id"
          class="dash-bar-item d-flex align-items-center"
        >
          <div class="flex-grow-1 min-w-0">
            <div class="d-flex justify-content-between align-items-baseline mb-1">
              <span class="dash-bar-name text-truncate">{{ u.nome }}</span>
              <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">R$ {{ formatCurrency(u.total) }}</span>
            </div>
            <div class="progress dash-bar-progress">
              <div
                class="progress-bar bg-info"
                :style="{ width: u.pct + '%' }"
              ></div>
            </div>
            <small class="text-muted">{{ u.count }} registro{{ u.count !== 1 ? 's' : '' }}</small>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 5: Distribuição por Entidade/Beneficiário ===== -->
    <div class="dash-section" v-if="entidadeDistribuicao.length">
      <div class="dash-section-title">
        <i class="fas fa-hand-holding-heart mr-2"></i>Distribuição por Entidade/Beneficiário
        <small v-if="entidadeDistribuicaoExtra > 0" class="text-muted ml-2">
          (top {{ entidadeDistribuicao.length }} de {{ entidadeDistribuicao.length + entidadeDistribuicaoExtra }})
        </small>
      </div>
      <div class="dash-bar-list">
        <div
          v-for="e in entidadeDistribuicao"
          :key="e.id"
          class="dash-bar-item d-flex align-items-center"
        >
          <div class="flex-grow-1 min-w-0">
            <div class="d-flex justify-content-between align-items-baseline mb-1">
              <span class="dash-bar-name text-truncate">{{ e.nome }}</span>
              <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">R$ {{ formatCurrency(e.total) }}</span>
            </div>
            <div class="progress dash-bar-progress">
              <div
                class="progress-bar bg-success"
                :style="{ width: e.pct + '%' }"
              ></div>
            </div>
            <small class="text-muted">{{ e.count }} registro{{ e.count !== 1 ? 's' : '' }}</small>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { isEmenda, faseLabel, situacaoLabel } from './utils/pcl-helpers'

const TOP_N = 10

const TIPO_SHORT = {
  0: 'Modificativa',
  10: 'Saúde',
  99: 'Áreas Diversas'
}

const DASH_SITUACAO_PALETTE = [
  '#4e79a7', // azul aço
  '#f28e2b', // laranja
  '#e15759', // vermelho coral
  '#59a14f', // verde
  '#76b7b2', // verde-água
  '#edc948', // amarelo
  '#b07aa1', // roxo
  '#ff9da7', // rosa
  '#9c755f', // marrom
  '#86bcb6', // ciano
  '#8cd17d', // verde claro
  '#d37295', // rosa escuro
  '#499894', // teal
  '#b6992d', // dourado
  '#bab0ac' // cinza
]

export default {
  name: 'pcl-dashboard',
  props: {
    lista: { type: Array, default: () => [] },
    parlamentarSelecionado: { type: Object, default: null }
  },
  computed: {
    kpis () {
      let totalSaude = 0; let countSaude = 0
      let totalAreasDiversas = 0; let countAreasDiversas = 0
      let totalModificativas = 0; let countModificativas = 0

      this.lista.forEach(item => {
        const val = Number(this.valorEfetivo(item))
        const tipo = item.tipo
        if (tipo === 10) { totalSaude += val; countSaude++ } else if (tipo === 99) { totalAreasDiversas += val; countAreasDiversas++ } else if (tipo === 0) { totalModificativas += val; countModificativas++ }
      })

      return {
        totalImpositivas: totalSaude + totalAreasDiversas,
        countImpositivas: countSaude + countAreasDiversas,
        totalSaude,
        countSaude,
        totalAreasDiversas,
        countAreasDiversas,
        totalModificativas,
        countModificativas
      }
    },

    faseDistribuicao () {
      const map = {}
      this.lista.forEach(item => {
        const emenda = isEmenda(item)
        const tipo = item.tipo
        const tipoLbl = TIPO_SHORT[tipo] || `Tipo ${tipo}`
        let key, label
        if (emenda) {
          key = `emenda_fase${item.fase}_tipo${tipo}`
          label = faseLabel(item.fase)
        } else {
          const sit = item.fase_prestacao_contas || 'SEM_PRESTACAO_CONTAS'
          key = `ajuste_sit${sit}_tipo${tipo}`
          label = situacaoLabel(sit)
        }
        if (!map[key]) {
          map[key] = {
            key,
            label,
            tipoLabel: emenda ? `Emenda ${tipoLbl}` : `Ajuste ${tipoLbl}`,
            count: 0,
            total: 0
          }
        }
        map[key].count++
        map[key].total += Number(this.valorEfetivo(item))
      })
      const total = this.lista.length || 1
      const sorted = Object.values(map).sort((a, b) => b.count - a.count)
      return sorted.map((f, i) => ({
        ...f,
        pct: (f.count / total) * 100,
        color: DASH_SITUACAO_PALETTE[i % DASH_SITUACAO_PALETTE.length]
      }))
    },

    parlamentarDistribuicao () {
      const map = {}
      this.lista.forEach(item => {
        const parlamentares = isEmenda(item) ? item.parlamentares : item.parlamentares_valor
        if (!parlamentares || !parlamentares.length) return
        const val = Number(this.valorEfetivo(item))
        const share = val / parlamentares.length
        parlamentares.forEach(p => {
          if (!map[p.id]) {
            map[p.id] = {
              id: p.id,
              nome: p.__str__ || p.nome_parlamentar || `Parlamentar ${p.id}`,
              fotografia: p.fotografia || null,
              total: 0,
              emendas: 0,
              ajustes: 0
            }
          }
          map[p.id].total += share
          if (isEmenda(item)) map[p.id].emendas++
          else map[p.id].ajustes++
        })
      })
      const list = Object.values(map).sort((a, b) => b.total - a.total)
      const max = list.length ? list[0].total : 1
      return list.map(p => ({ ...p, pct: (p.total / max) * 100 }))
    },

    unidadeDistribuicaoAll () {
      const map = {}
      this.lista.forEach(item => {
        const u = item.unidade
        if (!u) return
        const key = u.id
        if (!map[key]) {
          map[key] = { id: key, nome: u.__str__, total: 0, count: 0 }
        }
        map[key].total += Number(this.valorEfetivo(item))
        map[key].count++
      })
      return Object.values(map).sort((a, b) => b.total - a.total)
    },
    unidadeDistribuicao () {
      const all = this.unidadeDistribuicaoAll
      const top = all.slice(0, TOP_N)
      const max = top.length ? top[0].total : 1
      return top.map(u => ({ ...u, pct: (u.total / max) * 100 }))
    },
    unidadeDistribuicaoExtra () {
      return Math.max(0, this.unidadeDistribuicaoAll.length - TOP_N)
    },

    entidadeDistribuicaoAll () {
      const map = {}
      this.lista.forEach(item => {
        if (!isEmenda(item)) return
        const e = item.entidade
        if (!e || !e.nome_fantasia) return
        const key = e.id
        if (!map[key]) {
          map[key] = { id: key, nome: e.nome_fantasia, total: 0, count: 0 }
        }
        map[key].total += Number(this.valorEfetivo(item))
        map[key].count++
      })
      return Object.values(map).sort((a, b) => b.total - a.total)
    },
    entidadeDistribuicao () {
      const all = this.entidadeDistribuicaoAll
      const top = all.slice(0, TOP_N)
      const max = top.length ? top[0].total : 1
      return top.map(e => ({ ...e, pct: (e.total / max) * 100 }))
    },
    entidadeDistribuicaoExtra () {
      return Math.max(0, this.entidadeDistribuicaoAll.length - TOP_N)
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
      const valor_computado = Number(item.valor_computado || 0)
      if (item.has_ajustes || item.fase === 40) return valor_computado

      let valor_inicial = Number(item.valor_inicial || 0)
      if (this.parlamentarSelecionado && item.valor_inicial_por_parlamentar) {
        const vid = item.valor_inicial_por_parlamentar[this.parlamentarSelecionado.id]
        if (vid !== undefined) valor_inicial = Number(vid)
      }
      return valor_inicial
    },
    formatCurrency (value) {
      return Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    fotoThumb (foto) {
      if (!foto) return ''
      if (typeof foto === 'string') {
        return foto.replace('/media/', '/media/cache/') || foto
      }
      return foto.thumbnail || foto.original || ''
    }
  }
}
</script>

<style lang="scss" scoped>
.pcl-dashboard {
  margin: 15px -15px 30px;
}

.dash-section {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}
.dash-section-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: #333;
  margin-bottom: 0.75rem;
  padding-bottom: 0.4rem;
  border-bottom: 2px solid #e9ecef;
}

/* KPI Cards */
.dash-kpi-row {
  gap: 0.75rem;
}
.dash-kpi-card {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
  min-width: 180px;
}
.dash-kpi-icon {
  font-size: 1.5rem;
  margin-right: 0.75rem;
  opacity: 0.85;
}
.dash-kpi-label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #666;
}
.dash-kpi-value {
  font-size: 1.1rem;
  font-weight: 700;
}

/* Progress stacked bar */
.dash-progress-bar {
  height: 1.25rem;
  border-radius: 0.375rem;
}

/* Legend */
.dash-legend-item {
  font-size: 0.82rem;
  display: flex;
  align-items: center;
}
.dash-legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 0.35rem;
  flex-shrink: 0;
}
.dash-legend-label {
  color: #555;
}

/* Horizontal bar list */
.dash-bar-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.dash-bar-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
  &:last-child {
    border-bottom: none;
  }
}
.dash-bar-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.dash-bar-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #adb5bd;
  font-size: 0.9rem;
  flex-shrink: 0;
}
.dash-bar-name {
  font-size: 0.88rem;
  font-weight: 500;
  color: #333;
}
.dash-bar-value {
  font-size: 0.85rem;
  color: #212529;
}
.dash-bar-progress {
  height: 0.5rem;
  border-radius: 0.25rem;
  background: #e9ecef;
}
.min-w-0 {
  min-width: 0;
}

/* ===== Responsivo < 768px ===== */
@media (max-width: 767.98px) {
  .dash-kpi-row {
    flex-direction: column;
  }
  .dash-kpi-card {
    min-width: auto;
  }
  .dash-legend {
    flex-direction: column;
  }
}
</style>
