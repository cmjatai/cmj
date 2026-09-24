<template>
  <div class="pcl-dashboard" v-if="lista.length">

    <pcl-totalizacao
      v-if="lista.length"
      :lista="lista"
      :parlamentar-selecionado="parlamentarSelecionado"
      :loas-choice="loasChoice"
      :selected-loa-ids="selectedLoaIds"
      :totais-empenhos="totaisEmpenhos"
      class="mt-3 dash-section"
    />

    <!-- ===== SEÇÃO 1: KPIs ===== -->
    <div class="dash-section d-none">
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

    <!-- ===== SEÇÃO 2: Distribuição por Situação (Saúde e Áreas Diversas) ===== -->
    <div class="dash-section" v-if="faseSecoes.some(s => s.dados.length)">
      <div class="row">
        <div
          v-for="secao in faseSecoes"
          :key="secao.titulo"
          v-show="secao.dados.length"
          class="col-md-6"
        >
          <div class="dash-section-title">
            <i :class="['fas', secao.icon, 'mr-2']"></i>{{ secao.titulo }}
          </div>
          <div class="dash-bar-list">
            <div
              v-for="f in secao.dados"
              :key="f.key"
              class="dash-bar-item d-flex align-items-center"
            >
              <span class="dash-legend-dot mr-2" :style="{ backgroundColor: f.color }"></span>
              <div class="flex-grow-1 min-w-0">
                <div class="d-flex justify-content-between align-items-baseline mb-1">
                  <span class="dash-bar-name text-truncate">{{ f.label }}</span>
                  <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">
                    {{ f.count }} <small class="text-muted font-weight-normal">(R$ {{ formatCurrency(f.total) }})</small>
                  </span>
                </div>
                <div class="progress dash-bar-progress">
                  <div
                    class="progress-bar"
                    :style="{ width: f.pct + '%', backgroundColor: f.color }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 3: Distribuição por Parlamentar ===== -->
    <div class="dash-section" v-if="parlamentarDistribuicao.length">
      <div class="dash-section-title d-flex justify-content-between align-items-center">
        <span>
          <i class="fas fa-users mr-2"></i>Distribuição por Parlamentar em Áreas Diversas
          <small class="text-muted ml-2">(*50% são da Área da Saúde e não estão incluídos)</small>
        </span>
        <button
          type="button"
          class="btn btn-sm btn-link text-muted p-0 dash-toggle-all"
          @click="toggleTodosParlamentares"
        >
          <i :class="['fas', todosParlamentaresExpandidos ? 'fa-compress-alt' : 'fa-expand-alt', 'mr-1']"></i>
          {{ todosParlamentaresExpandidos ? 'Recolher todos' : 'Expandir todos' }}
        </button>
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
            <div
              class="progress dash-bar-progress dash-bar-progress--clickable"
              role="button"
              @click="toggleParlamentarDetalhe(p.id)"
            >
              <div
                v-for="seg in p.segmentos"
                :key="seg.key"
                class="progress-bar"
                :title="`${seg.label}: R$ ${formatCurrency(seg.total)}`"
                :style="{ width: seg.pct + '%', backgroundColor: seg.color }"
              ></div>
            </div>
            <small class="text-muted">
              {{ p.emendas }} emenda{{ p.emendas !== 1 ? 's' : '' }},
              {{ p.ajustes }} ajuste{{ p.ajustes !== 1 ? 's' : '' }}
            </small>
            <table v-if="isParlamentarExpandido(p.id)" class="table table-sm dash-bar-detalhe mb-0 mt-2">
              <thead>
                <tr>
                  <th>Unidade</th>
                  <th class="text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="seg in p.segmentos" :key="seg.key">
                  <td>{{ seg.label }}</td>
                  <td class="d-flex text-nowrap justify-content-between">
                    <small class="text-muted">({{ formatPercent(seg.total, p.total) }}%)</small>
                    <span>
                      R$ {{ formatCurrency(seg.total) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== SEÇÃO 4 e 5: Distribuição por Unidade Orçamentária / Entidade-Beneficiário ===== -->
    <div class="row" v-if="unidadeDistribuicao.length || entidadeDistribuicao.length">
      <div class="col-md-6" v-if="unidadeDistribuicao.length">
        <div class="dash-section">
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
      </div>

      <div class="col-md-6" v-if="entidadeDistribuicao.length">
        <div class="dash-section">
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
    </div>

  </div>
</template>

<script>
import { isEmenda, faseLabel, situacaoLabel } from '../utils/pcl-helpers'
import PclTotalizacao from './PclTotalizacao.vue'
const TOP_N = 10

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
  components: {
    PclTotalizacao
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
      parlamentaresExpandidos: []
    }
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

    faseSecoes () {
      return [
        { titulo: 'Situação — Saúde', icon: 'fa-heartbeat', dados: this.distribuicaoPorFase(10) },
        { titulo: 'Situação — Áreas Diversas', icon: 'fa-th-large', dados: this.distribuicaoPorFase(99) }
      ]
    },

    parlamentarDistribuicao () {
      const map = {}
      const unidadeTotais = {}
      // apenas emendas/ajustes de 99 (Áreas Diversas) entram na soma
      const itensValidos = this.lista.filter(item => item.tipo === 99)
      itensValidos.forEach(item => {
        const parlamentares = isEmenda(item) ? item.parlamentares : item.parlamentares_valor
        if (!parlamentares || !parlamentares.length) return
        const val = Number(this.valorEfetivo(item))
        const unidadeKey = item.unidade ? item.unidade.id : 'sem-unidade'
        const unidadeLabel = item.unidade ? item.unidade.__str__ : 'Sem unidade'
        if (!unidadeTotais[unidadeKey]) unidadeTotais[unidadeKey] = { label: unidadeLabel, total: 0 }
        unidadeTotais[unidadeKey].total += val
        parlamentares.forEach(p => {
          if (!map[p.id]) {
            map[p.id] = {
              id: p.id,
              nome: p.__str__ || p.nome_parlamentar || `Parlamentar ${p.id}`,
              fotografia: p.fotografia || null,
              total: 0,
              emendas: 0,
              ajustes: 0,
              unidades: {}
            }
          }
          const valorParlamentar = this.valorEfetivoPorParlamentar(item, p.id)
          map[p.id].total += valorParlamentar
          if (!map[p.id].unidades[unidadeKey]) map[p.id].unidades[unidadeKey] = { label: unidadeLabel, total: 0 }
          map[p.id].unidades[unidadeKey].total += valorParlamentar
          if (isEmenda(item)) map[p.id].emendas++
          else map[p.id].ajustes++
        })
      })

      // cores fixas por unidade, na mesma ordem em todos os parlamentares
      const unidadeKeys = Object.keys(unidadeTotais).sort((a, b) => unidadeTotais[b].total - unidadeTotais[a].total)
      const corPorUnidade = {}
      unidadeKeys.forEach((key, i) => {
        corPorUnidade[key] = DASH_SITUACAO_PALETTE[i % DASH_SITUACAO_PALETTE.length]
      })

      const list = Object.values(map).sort((a, b) => b.total - a.total)
      const max = list.length ? list[0].total : 1
      return list.map(({ unidades, ...p }) => {
        const segmentos = Object.entries(unidades)
          .map(([key, u]) => ({
            key,
            label: u.label,
            total: u.total,
            pct: (u.total / max) * 100,
            color: corPorUnidade[key]
          }))
          .sort((a, b) => b.total - a.total)
        return { ...p, pct: (p.total / max) * 100, segmentos }
      })
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
    },

    todosParlamentaresExpandidos () {
      return this.parlamentarDistribuicao.length > 0 &&
        this.parlamentaresExpandidos.length >= this.parlamentarDistribuicao.length
    }
  },
  methods: {
    // Agrupa emenda + ajuste do mesmo tipo por fase/situação, sem distinguir a origem do documento
    distribuicaoPorFase (tipo) {
      const map = {}
      this.lista.forEach(item => {
        if (item.tipo !== tipo) return
        const label = isEmenda(item)
          ? faseLabel(item.fase)
          : situacaoLabel(item.fase_prestacao_contas || 'Ajustes Sem Prestação de Contas')
        if (!map[label]) {
          map[label] = { key: label, label, count: 0, total: 0 }
        }
        map[label].count++
        map[label].total += Number(this.valorEfetivo(item))
      })
      const sorted = Object.values(map).sort((a, b) => b.count - a.count)
      const max = sorted.length ? sorted[0].count : 1
      return sorted.map((f, i) => ({
        ...f,
        pct: (f.count / max) * 100,
        color: DASH_SITUACAO_PALETTE[i % DASH_SITUACAO_PALETTE.length]
      }))
    },
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
    // Valor de um item atribuído a um parlamentar específico (independente do parlamentarSelecionado)
    valorEfetivoPorParlamentar (item, parlamentarId) {
      if (!isEmenda(item)) {
        const vp = item.valor_por_parlamentar && item.valor_por_parlamentar[parlamentarId]
        return vp !== undefined ? Number(vp) : 0
      }
      const valorInicialTotal = Number(item.valor_inicial || 0)
      const vip = item.valor_inicial_por_parlamentar && item.valor_inicial_por_parlamentar[parlamentarId]
      const valorInicialParlamentar = vip !== undefined ? Number(vip) : 0

      if (item.has_ajustes || item.fase === 40) {
        if (!valorInicialTotal) return 0
        const valor_computado = Number(item.valor_computado || 0)
        // mantém a proporção original do parlamentar aplicada ao valor computado
        return (valorInicialParlamentar / valorInicialTotal) * valor_computado
      }
      return valorInicialParlamentar
    },
    formatCurrency (value) {
      return Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    formatPercent (value, total) {
      if (!total) return '0,0'
      return (Number(value) / Number(total) * 100).toLocaleString('pt-BR', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
      })
    },
    fotoThumb (foto) {
      if (!foto) return ''
      if (typeof foto === 'string') {
        return foto.replace('/media/', '/media/cache/') || foto
      }
      return foto.thumbnail || foto.original || ''
    },
    toggleParlamentarDetalhe (id) {
      const idx = this.parlamentaresExpandidos.indexOf(id)
      if (idx === -1) this.parlamentaresExpandidos.push(id)
      else this.parlamentaresExpandidos.splice(idx, 1)
    },
    isParlamentarExpandido (id) {
      return this.parlamentaresExpandidos.includes(id)
    },
    toggleTodosParlamentares () {
      this.parlamentaresExpandidos = this.todosParlamentaresExpandidos
        ? []
        : this.parlamentarDistribuicao.map(p => p.id)
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
.dash-toggle-all {
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  &:hover {
    text-decoration: none;
    color: #495057 !important;
  }
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

/* Legend dot (usado nas linhas da Seção 2) */
.dash-legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
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
.dash-bar-progress--clickable {
  cursor: pointer;
  transition: opacity 0.15s ease-in-out;
  &:hover {
    opacity: 0.8;
  }
}
.dash-bar-detalhe {
  font-size: 0.82rem;
  th {
    font-weight: 600;
    color: #666;
    border-top: none;
    padding: 0.3rem 0.5rem;
  }
  td {
    padding: 0.3rem 0.5rem;
  }
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
}
</style>
