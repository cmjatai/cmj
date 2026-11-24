<template>
  <div class="pcl-dashboard" v-if="dados">

    <pcl-totalizacao
      v-if="resumo"
      :resumo="resumo"
      class="mt-3 dash-section"
    />

    <!-- ===== SEÇÃO 2: Distribuição por Situação (Saúde e Áreas Diversas) ===== -->
    <div class="dash-section" v-if="faseSecoes.some(s => s.dados.length)">
      <div class="row">
        <div
          v-for="secao in faseSecoes"
          :key="secao.titulo"
          v-show="secao.dados.length"
          :class="[`col-md-${faseSecoes.every(s => s.dados.length) ? 6 : 12}`]"
        >
          <div class="dash-section-title d-flex justify-content-between align-items-center">
            <span>
              <i :class="['fas', secao.icon, 'mr-2']"></i>{{ secao.titulo }}<br>
              <small class="text-muted">(Emendas Impositivas e Ajustes Técnicos)</small>
            </span>
            <button
              type="button"
              class="btn btn-sm btn-link text-muted p-0 dash-toggle-all"
              @click="toggleTodasSituacoes(secao)"
            >
              <i :class="['fas', todasSituacoesExpandidas(secao) ? 'fa-compress-alt' : 'fa-expand-alt', 'mr-1']"></i>
              {{ todasSituacoesExpandidas(secao) ? 'Recolher todos' : 'Expandir todos' }}
            </button>
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
                <div
                  class="progress dash-bar-progress dash-bar-progress--clickable"
                  role="button"
                  @click="toggleSituacaoDetalhe(secao.titulo, f.key)"
                >
                  <div
                    class="progress-bar"
                    :style="{ width: f.pct + '%', backgroundColor: f.color }"
                  ></div>
                </div>
                <table v-if="isSituacaoExpandida(secao.titulo, f.key)" class="table table-sm dash-bar-detalhe mb-0 mt-2">
                  <thead>
                    <tr>
                      <th>Parlamentar</th>
                      <th class="text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="seg in f.parlamentares" :key="seg.key">
                      <td
                        class="dash-bar-detalhe-link"
                        title="Filtrar por este parlamentar"
                        @click="$emit('filter-parlamentar', { id: seg.key, __str__: seg.label })"
                      >{{ seg.label }}</td>
                      <td class="d-flex text-nowrap justify-content-between">
                        <small class="text-muted">({{ formatPercent(seg.total, f.total) }}%)</small>
                        <span>R$ {{ formatCurrency(seg.total) }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
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
          <small class="text-muted ml-2">(50% da Área da Saúde não estão incluídos)</small>
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
              <span
                class="dash-bar-name dash-bar-name--clickable text-truncate"
                title="Filtrar por este parlamentar"
                @click="$emit('filter-parlamentar', { id: p.id, __str__: p.nome })"
              >{{ p.nome }}</span>
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
                :class="{ 'dash-bar-segmento--hover': isSegmentoHover(p.id, seg.key) }"
                :title="`${seg.label}: R$ ${formatCurrency(seg.total)}`"
                :style="{ width: seg.pct + '%', backgroundColor: seg.color }"
                @mouseenter="setSegmentoHover(p.id, seg.key)"
                @mouseleave="clearSegmentoHover"
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
                <tr
                  v-for="seg in p.segmentos"
                  :key="seg.key"
                  :class="{ 'dash-bar-detalhe-hover': isSegmentoHover(p.id, seg.key) }"
                  @mouseenter="setSegmentoHover(p.id, seg.key)"
                  @mouseleave="clearSegmentoHover"
                >
                  <td
                    :class="{ 'dash-bar-detalhe-link': seg.key !== 'sem-unidade' }"
                    :title="seg.key !== 'sem-unidade' ? 'Filtrar por esta unidade' : ''"
                    @click="seg.key !== 'sem-unidade' && $emit('filter-unidade', { id: seg.key, __str__: seg.label })"
                  >{{ seg.label }}</td>
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
    <div class="dash-grid-tight" v-if="unidadeDistribuicao.length || entidadeDistribuicao.length">
      <div class="col-md-6" v-if="unidadeDistribuicao.length">
        <div class="dash-section">
          <div class="dash-section-title d-flex justify-content-between align-items-center">
            <div class="d-flex flex-column">
              <span>
                <i class="fas fa-building mr-2"></i>Distribuição por Unidade Orçamentária
                <small v-if="unidadeDistribuicaoExtra > 0" class="text-muted ml-2">
                  (top {{ unidadeDistribuicao.length }} de {{ unidadeDistribuicao.length + unidadeDistribuicaoExtra }})
                </small>
              </span>
              <small class="text-muted">*Apenas unidades orçamentárias das Áreas Diversas</small>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-link text-muted p-0 dash-toggle-all"
              @click="toggleTodasUnidades"
            >
              <i :class="['fas', todasUnidadesExpandidas ? 'fa-compress-alt' : 'fa-expand-alt', 'mr-1']"></i>
              {{ todasUnidadesExpandidas ? 'Recolher todos' : 'Expandir todos' }}
            </button>
          </div>
          <div class="dash-bar-list">
            <div
              v-for="u in unidadeDistribuicao"
              :key="u.id"
              class="dash-bar-item d-flex align-items-center"
            >
              <div class="flex-grow-1 min-w-0">
                <div class="d-flex justify-content-between align-items-baseline mb-1">
                  <span
                    class="dash-bar-name dash-bar-name--clickable text-truncate"
                    title="Filtrar por esta unidade"
                    @click="$emit('filter-unidade', { id: u.id, __str__: u.nome })"
                  >{{ u.nome }}</span>
                  <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">R$ {{ formatCurrency(u.total) }}</span>
                </div>
                <div
                  class="progress dash-bar-progress dash-bar-progress--clickable"
                  role="button"
                  @click="toggleUnidadeDetalhe(u.id)"
                >
                  <div
                    class="progress-bar bg-info"
                    :style="{ width: u.pct + '%' }"
                  ></div>
                </div>
                <small class="text-muted">{{ u.count }} registro{{ u.count !== 1 ? 's' : '' }}</small>
                <table v-if="isUnidadeExpandida(u.id)" class="table table-sm dash-bar-detalhe mb-0 mt-2">
                  <thead>
                    <tr>
                      <th>Parlamentar</th>
                      <th class="text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="seg in u.parlamentares" :key="seg.key">
                      <td
                        class="dash-bar-detalhe-link"
                        title="Filtrar por este parlamentar"
                        @click="$emit('filter-parlamentar', { id: seg.key, __str__: seg.label })"
                      >{{ seg.label }}</td>
                      <td class="d-flex text-nowrap justify-content-between">
                        <small class="text-muted">({{ formatPercent(seg.total, u.total) }}%)</small>
                        <span>R$ {{ formatCurrency(seg.total) }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6" v-if="entidadeDistribuicao.length">
        <div class="dash-section">
          <div class="dash-section-title d-flex justify-content-between align-items-center">
            <div class="d-flex flex-column">
              <span>
                <i class="fas fa-hand-holding-heart mr-2"></i>Distribuição por Entidade/Beneficiário
                <small v-if="entidadeDistribuicaoExtra > 0" class="text-muted ml-2">
                  (top {{ entidadeDistribuicao.length }} de {{ entidadeDistribuicao.length + entidadeDistribuicaoExtra }})
                </small>
              </span>
              <small class="text-muted">*Inclui entidades da Área da Saúde e de Áreas Diversas</small>
            </div>
            <button
              type="button"
              class="btn btn-sm btn-link text-muted p-0 dash-toggle-all"
              @click="toggleTodasEntidades"
            >
              <i :class="['fas', todasEntidadesExpandidas ? 'fa-compress-alt' : 'fa-expand-alt', 'mr-1']"></i>
              {{ todasEntidadesExpandidas ? 'Recolher todos' : 'Expandir todos' }}
            </button>
          </div>
          <div class="dash-bar-list">
            <div
              v-for="e in entidadeDistribuicao"
              :key="e.id"
              class="dash-bar-item d-flex align-items-center"
            >
              <div class="flex-grow-1 min-w-0">
                <div class="d-flex justify-content-between align-items-baseline mb-1">
                  <span
                    class="dash-bar-name dash-bar-name--clickable text-truncate"
                    title="Filtrar por esta entidade"
                    @click="$emit('filter-entidade', { id: e.id, __str__: e.nome })"
                  >{{ e.nome }}</span>
                  <span class="dash-bar-value font-weight-bold ml-2 text-nowrap">R$ {{ formatCurrency(e.total) }}</span>
                </div>
                <div
                  class="progress dash-bar-progress dash-bar-progress--clickable"
                  role="button"
                  @click="toggleEntidadeDetalhe(e.id)"
                >
                  <div
                    class="progress-bar bg-success"
                    :style="{ width: e.pct + '%' }"
                  ></div>
                </div>
                <small class="text-muted">{{ e.count }} registro{{ e.count !== 1 ? 's' : '' }}</small>
                <table v-if="isEntidadeExpandida(e.id)" class="table table-sm dash-bar-detalhe mb-0 mt-2">
                  <thead>
                    <tr>
                      <th>Parlamentar</th>
                      <th class="text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="seg in e.parlamentares" :key="seg.key">
                      <td
                        class="dash-bar-detalhe-link"
                        title="Filtrar por este parlamentar"
                        @click="$emit('filter-parlamentar', { id: seg.key, __str__: seg.label })"
                      >{{ seg.label }}</td>
                      <td class="d-flex text-nowrap justify-content-between">
                        <small class="text-muted">({{ formatPercent(seg.total, e.total) }}%)</small>
                        <span>R$ {{ formatCurrency(seg.total) }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="dash-section">
      <h3>OBS: Os dados acima são computados com base nas Emendas Impositivas e Ajustes Técnicos.</h3>
      <h4>Outros gráficos que comporão o dashboard estão em desenvolvimento para correlacionar com os Empenhos.</h4>
    </div>

  </div>
</template>

<script>
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
  // Só apresenta: as distribuições vêm prontas do backend
  // (prestacaoconta_dashboard, docs/specs/loa/prestacao-contas-consulta.md).
  // Aqui ficam o corte nas maiores, as barras proporcionais e as cores.
  props: {
    dados: { type: Object, default: null },
    resumo: { type: Object, default: null },
    parlamentarSelecionado: { type: Object, default: null },
    selectedLoaIds: { type: Array, default: () => [] }
  },
  data () {
    return {
      parlamentaresExpandidos: [],
      unidadesExpandidas: [],
      entidadesExpandidas: [],
      situacoesExpandidas: [],
      segmentoHover: null
    }
  },
  computed: {
    faseSecoes () {
      const secoes = {
        10: { titulo: 'Situação — Saúde', icon: 'fa-heartbeat' },
        99: { titulo: 'Situação — Áreas Diversas', icon: 'fa-th-large' }
      }
      return [10, 99].map(tipo => {
        const secao = (this.dados.situacao || []).find(s => s.tipo === tipo)
        const grupos = secao ? secao.grupos : []
        const max = (grupos.length && grupos[0].quantidade) || 1
        return {
          ...secoes[tipo],
          dados: grupos.map((g, i) => ({
            key: g.chave,
            label: g.rotulo,
            count: g.quantidade,
            total: Number(g.valor),
            pct: (g.quantidade / max) * 100,
            color: DASH_SITUACAO_PALETTE[i % DASH_SITUACAO_PALETTE.length],
            parlamentares: this.porParlamentar(g.parlamentares)
          }))
        }
      })
    },

    parlamentarDistribuicao () {
      const lista = this.dados.parlamentares || []
      const chave = u => (u.id === null ? 'sem-unidade' : u.id)

      // cores fixas por unidade, na mesma ordem em todos os parlamentares
      const totalPorUnidade = {}
      lista.forEach(p => p.unidades.forEach(u => {
        totalPorUnidade[chave(u)] = (totalPorUnidade[chave(u)] || 0) + Number(u.valor)
      }))
      const corPorUnidade = {}
      Object.keys(totalPorUnidade)
        .sort((a, b) => totalPorUnidade[b] - totalPorUnidade[a])
        .forEach((key, i) => {
          corPorUnidade[key] = DASH_SITUACAO_PALETTE[i % DASH_SITUACAO_PALETTE.length]
        })

      const variosExercicios = this.selectedLoaIds.length > 1
      const max = (lista.length && Number(lista[0].valor)) || 1
      return lista.map(p => {
        const total = Number(p.valor)
        return {
          id: p.id,
          nome: p.nome,
          fotografia: p.fotografia,
          total,
          emendas: p.emendas,
          ajustes: p.ajustes,
          pct: (total / max) * 100,
          segmentos: p.unidades.map(u => ({
            key: chave(u),
            label: u.id === null
              ? 'Sem unidade'
              : `${u.nome}${variosExercicios ? ` (${u.ano})` : ''}`,
            total: Number(u.valor),
            pct: (Number(u.valor) / max) * 100,
            color: corPorUnidade[chave(u)]
          }))
        }
      })
    },

    unidadeDistribuicaoAll () {
      return this.comBarra(this.dados.unidades || [])
    },
    unidadeDistribuicao () {
      return this.asMaiores(this.unidadeDistribuicaoAll)
    },
    unidadeDistribuicaoExtra () {
      if (this.parlamentarSelecionado) return 0
      return Math.max(0, this.unidadeDistribuicaoAll.length - TOP_N)
    },

    entidadeDistribuicaoAll () {
      return this.comBarra(this.dados.entidades || [])
    },
    entidadeDistribuicao () {
      return this.asMaiores(this.entidadeDistribuicaoAll)
    },
    entidadeDistribuicaoExtra () {
      if (this.parlamentarSelecionado) return 0
      return Math.max(0, this.entidadeDistribuicaoAll.length - TOP_N)
    },

    todosParlamentaresExpandidos () {
      return this.parlamentarDistribuicao.length > 0 &&
        this.parlamentaresExpandidos.length >= this.parlamentarDistribuicao.length
    },

    todasUnidadesExpandidas () {
      return this.unidadeDistribuicao.length > 0 &&
        this.unidadesExpandidas.length >= this.unidadeDistribuicao.length
    },

    todasEntidadesExpandidas () {
      return this.entidadeDistribuicao.length > 0 &&
        this.entidadesExpandidas.length >= this.entidadeDistribuicao.length
    }
  },
  methods: {
    // Parlamentares de um grupo, no formato das tabelas de detalhe
    porParlamentar (parlamentares) {
      return (parlamentares || []).map(p => ({
        key: p.id,
        label: p.nome,
        total: Number(p.valor)
      }))
    },
    // Lista do backend (já do maior para o menor), no formato das barras
    comBarra (lista) {
      return lista.map(item => ({
        id: item.id,
        nome: item.nome,
        total: Number(item.valor),
        count: item.quantidade,
        parlamentares: this.porParlamentar(item.parlamentares)
      }))
    },
    // As dez maiores, ou todas quando há filtro de parlamentar
    asMaiores (todas) {
      const lista = this.parlamentarSelecionado ? todas : todas.slice(0, TOP_N)
      const max = (lista.length && lista[0].total) || 1
      return lista.map(item => ({ ...item, pct: (item.total / max) * 100 }))
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
        maximumFractionDigits: 2
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
    },
    setSegmentoHover (parlamentarId, segKey) {
      this.segmentoHover = parlamentarId + '|' + segKey
    },
    clearSegmentoHover () {
      this.segmentoHover = null
    },
    isSegmentoHover (parlamentarId, segKey) {
      return this.segmentoHover === (parlamentarId + '|' + segKey)
    },
    toggleUnidadeDetalhe (id) {
      const idx = this.unidadesExpandidas.indexOf(id)
      if (idx === -1) this.unidadesExpandidas.push(id)
      else this.unidadesExpandidas.splice(idx, 1)
    },
    isUnidadeExpandida (id) {
      return this.unidadesExpandidas.includes(id)
    },
    toggleTodasUnidades () {
      this.unidadesExpandidas = this.todasUnidadesExpandidas
        ? []
        : this.unidadeDistribuicao.map(u => u.id)
    },
    toggleEntidadeDetalhe (id) {
      const idx = this.entidadesExpandidas.indexOf(id)
      if (idx === -1) this.entidadesExpandidas.push(id)
      else this.entidadesExpandidas.splice(idx, 1)
    },
    isEntidadeExpandida (id) {
      return this.entidadesExpandidas.includes(id)
    },
    toggleTodasEntidades () {
      this.entidadesExpandidas = this.todasEntidadesExpandidas
        ? []
        : this.entidadeDistribuicao.map(e => e.id)
    },
    toggleSituacaoDetalhe (secaoTitulo, key) {
      const id = `${secaoTitulo}|${key}`
      const idx = this.situacoesExpandidas.indexOf(id)
      if (idx === -1) this.situacoesExpandidas.push(id)
      else this.situacoesExpandidas.splice(idx, 1)
    },
    isSituacaoExpandida (secaoTitulo, key) {
      return this.situacoesExpandidas.includes(`${secaoTitulo}|${key}`)
    },
    todasSituacoesExpandidas (secao) {
      return secao.dados.length > 0 &&
        secao.dados.every(f => this.isSituacaoExpandida(secao.titulo, f.key))
    },
    toggleTodasSituacoes (secao) {
      const ids = secao.dados.map(f => `${secao.titulo}|${f.key}`)
      if (this.todasSituacoesExpandidas(secao)) {
        this.situacoesExpandidas = this.situacoesExpandidas.filter(id => !ids.includes(id))
      } else {
        const novos = ids.filter(id => !this.situacoesExpandidas.includes(id))
        this.situacoesExpandidas = [...this.situacoesExpandidas, ...novos]
      }
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
/* Reduz o gutter padrão do bootstrap (30px) para igualar ao espaço vertical entre seções (1rem) */
.dash-grid-tight {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  > [class*='col-md'] {
    padding: 0;
    // flex: 1 1 calc(50% - 2rem);
    max-width: calc(50% - 0.5rem);
  }
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
  border-bottom: 1px solid #e5e5ef;
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
.dash-bar-name--clickable {
  cursor: pointer;
  &:hover {
    text-decoration: underline;
    color: #495057;
  }
}
.dash-bar-detalhe-link {
  cursor: pointer;
  &:hover {
    text-decoration: underline;
    color: #495057;
  }
}
.dash-bar-value {
  font-size: 0.85rem;
  color: #212529;
}
.dash-bar-progress {
  height: 0.5rem;
  border-radius: 0.25rem;
  background: #e9ecef;
  overflow: visible; // permite o zoom do segmento em hover sem ser cortado
}
.dash-bar-progress--clickable {
  cursor: pointer;
  transition: opacity 0.15s ease-in-out;
  &:hover {
    opacity: 0.8;
  }
  .progress-bar {
    transition: transform 0.15s ease-in-out, filter 0.15s ease-in-out;
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
.dash-bar-detalhe-hover {
  background-color: #eef3f8;
}
.dash-bar-segmento--hover {
  filter: brightness(0.85);
  transform: scaleY(1.6);
  transform-origin: center;
  position: relative;
  z-index: 1;
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
  .dash-grid-tight {
    display: flex;
    gap: 0rem;
    > [class*='col-md'] {
      flex: 1 1 100%;
      max-width: 100%;
    }
  }
  .dash-section {
    margin: 0.25rem 0.5rem;
    .col-md-6 {
      padding-top: 1rem;
    }
    table {
      display: table;
      width: 100%;
    }
  }
}
</style>
