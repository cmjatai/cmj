<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <pcl-filtros
        ref="filtros"
        :disabled="!ready || !firstPageLoaded"
        v-model="filters_value"
        :parlamentares-choice="parlamentares_choice"
        :entidades-choice="entidades_choice"
        :unidades-choice="unidades_choice"
        :loas-choice="loas_choice"
        :selected-loa-ids="selected_loa_ids"
        :locked-loa-id="loa.id"
        :total-items="total_itens"
        :page-size="pageSize"
        :current-page="currentPage"
        :fetching="fetching"
        :view-mode="viewMode"
        @update:page-size="onPageSizeChange"
        @update:current-page="onPageChange"
        @update:view-mode="val => viewModeChange(val)"
        @reset="resetFilters"
        @loas-change="on_loas_change"
      />
      <div v-if="erro" class="pcl-erro card text-center my-3 p-3 mx-5">
        <span class="font-weight-bold text-danger">
          <i class="fas fa-exclamation-triangle mr-1"></i>Não foi possível carregar os dados da prestação de contas.
        </span>
        <div class="mt-2">
          <button type="button" class="btn btn-sm btn-outline-primary" @click="fetch()">Tentar novamente</button>
        </div>
      </div>
      <pcl-totalizacao
        v-if="resumo && viewMode === 'list'"
        :resumo="resumo"
        class="mt-3 dash-section"
      />
      <pcl-dashboard
        v-if="filters_value.dash_activated && viewMode === 'dashboard' && dashboard && resumo && resumo.itens"
        :dados="dashboard"
        :parlamentar-selecionado="filters_value.parlamentares"
        :selected-loa-ids="selected_loa_ids"
        :resumo="resumo"
        @filter-unidade="applyUnidadeFilter"
        @filter-entidade="applyEntidadeFilter"
        @filter-parlamentar="applyParlamentarFilter"
      />
      <div class="pcldetalhe-list" v-else-if="viewMode === 'list' && (itens.length || fetching)">
        <template v-for="item in itens">
          <pcl-detalhe-emenda
            v-if="item.__label__ === 'loa_emendaloa'"
            :key="`emenda_${item.id}`"
            :registro="item"
            :unidade-filter-disabled="selected_loa_ids.length > 1"
            @filter-unidade="applyUnidadeFilter"
            @filter-entidade="applyEntidadeFilter"
            @filter-parlamentar="applyParlamentarFilter"
            @search-emenda="val => filters_value = { ...filters_value, search: val, ajustes: 'False', emendas_tipos: [] }"
          />
          <pcl-detalhe-ajuste
            v-else
            :key="`ajuste_${item.id}`"
            :registro="item"
            :unidade-filter-disabled="selected_loa_ids.length > 1"
            @search-emenda="val => filters_value = { ...filters_value, search: val , ajustes: 'False', emendas_tipos: [] }"
            @filter-unidade="applyUnidadeFilter"
            @filter-parlamentar="applyParlamentarFilter"
          />
        </template>
      </div>
      <div v-else-if="ready && viewMode === 'list' && !erro" class="card text-muted text-center my-3 p-3 mx-5 font-weight-bold">
        Nenhum resultado encontrado para os filtros selecionados.
      </div>
    </div>
    <div v-else-if="erro" class="pcl-erro card text-center my-3 p-3 mx-5">
      <span class="font-weight-bold text-danger">
        <i class="fas fa-exclamation-triangle mr-1"></i>Não foi possível carregar os dados da prestação de contas.
      </span>
      <div class="mt-2">
        <button type="button" class="btn btn-sm btn-outline-primary" @click="carregar()">Tentar novamente</button>
      </div>
    </div>
  </div>
</template>

<script>
import PclFiltros from './PclFiltros.vue'
import PclDetalheEmenda from './PclDetalheEmenda.vue'
import PclDetalheAjuste from './PclDetalheAjuste.vue'
import PclDashboard from './dash/PclDashboard.vue'
import PclTotalizacao from './dash/PclTotalizacao.vue'

export default {
  name: 'prestacaocontaloa-layout',
  components: {
    PclFiltros,
    PclDetalheEmenda,
    PclDetalheAjuste,
    PclDashboard,
    PclTotalizacao
  },
  data () {
    return {
      loa: { id: this.$route.params.pkloa },
      loas_list: [],
      selected_loa_ids: [],
      // opções dos seletores de filtro para os exercícios selecionados
      // (prestacaoconta_opcoes)
      opcoes: { parlamentares: [], unidades: [], entidades: [] },
      ready: false,
      viewMode: 'list',
      dash_activated: true,
      filters_value: {
        dash_activated: true,
        unidade: null,
        entidade: null,
        parlamentares: null,
        situacao: [],
        emendas_tipos: [],
        ajustes: 'False',
        search: ''
      },
      filters: [
        'unidade',
        'entidade',
        'parlamentares',
        'situacao',
        'emendas_tipos',
        'ajustes',
        'search'
      ],
      // a página de cartões em exibição e o total da seleção, ambos do
      // backend (prestacaoconta_itens): a paginação é do servidor
      itens: [],
      total_itens: 0,
      // totalização e execução, calculadas no backend (prestacaoconta_resumo)
      resumo: null,
      // distribuições do dashboard (prestacaoconta_dashboard), pedidas só
      // quando o modo dashboard está aberto
      dashboard: null,
      // falha numa requisição da carga inicial ou da busca: a tela avisa e
      // oferece repetir
      erro: false,
      fetching: false,
      firstPageLoaded: false,
      currentPage: 1,
      pageSize: Number(localStorage.getItem('portalcmj_page_size')) || 10
    }
  },
  computed: {
    loas_choice () {
      if (!this.loas_list.length) return []
      return this.loas_list.map(l => ({
        value: l.id,
        text: l.ano
      }))
    },
    parlamentares_choice () {
      return this.comOpcaoVazia(this.opcoes.parlamentares.map((p) => ({
        value: { id: p.id, nome_parlamentar: p.nome, __str__: p.nome },
        text: p.nome
      })), this.opcoes.parlamentares.length > 1)
    },
    entidades_choice () {
      return this.comOpcaoVazia(this.opcoes.entidades.map((e) => ({
        value: { id: e.id, nome_fantasia: e.nome, __str__: e.rotulo },
        text: e.rotulo
      })))
    },
    unidades_choice () {
      return this.comOpcaoVazia(this.opcoes.unidades.map((u) => ({
        value: { id: u.id, __str__: u.nome },
        text: u.nome
      })))
    }
  },
  watch: {
    filters_value: {
      deep: true,
      handler (nv, ov) {
        if (!this.ready) return
        this.currentPage = 1
        this.syncQueryString()
        this.fetch()
      }
    }
  },
  methods: {
    comOpcaoVazia (opcoes, comVazia = true) {
      return comVazia ? [{ value: null, text: '----------------' }, ...opcoes] : opcoes
    },
    // Opções dos seletores para os exercícios selecionados. Filtro que ficou
    // sem a sua opção (exercício desmarcado) é descartado; devolve `true`
    // quando descartou algum, caso em que o observador dos filtros já refaz
    // a busca.
    fetchOpcoes () {
      const extras = this.selected_loa_ids.filter(id => id !== this.loa.id)
      return this.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: this.loa.id,
        action: 'prestacaoconta_opcoes',
        params: extras.length ? { loas: extras.join(',') } : {}
      }).then((response) => {
        this.opcoes = { parlamentares: [], unidades: [], entidades: [], ...response.data }
        return this.descartarFiltrosSemOpcao()
      }).catch((error) => {
        this.opcoes = { parlamentares: [], unidades: [], entidades: [] }
        this.registrarFalha(error)
        return false
      })
    },
    descartarFiltrosSemOpcao () {
      const sem = {}
      const confere = (filtro, opcoes) => {
        const atual = this.filters_value[filtro]
        if (atual && typeof atual === 'object' && !opcoes.some(o => o.id === atual.id)) sem[filtro] = null
      }
      confere('parlamentares', this.opcoes.parlamentares)
      confere('entidade', this.opcoes.entidades)
      confere('unidade', this.opcoes.unidades)
      if (!Object.keys(sem).length) return false
      this.filters_value = { ...this.filters_value, ...sem }
      return true
    },
    viewModeChange (val) {
      // armazena o valor do modo de visualização no localstorage
      localStorage.setItem('portalcmj_pcl_view_mode', val)
      this.viewMode = val
      this.syncQueryString()
      // os filtros podem ter mudado enquanto o dashboard estava fechado
      if (val === 'dashboard' && this.ready && !this.dashboard) {
        this.fetchDashboard(this._fetchId)
      }
    },
    viewModeRestore () {
      // restaura o valor do modo de visualização a partir da url ou, na ausência, do localstorage
      // NÃO chamar syncQueryString() aqui: nesse ponto do mounted() os demais filtros
      // ainda não foram lidos da querystring (applyQueryFilters roda depois), e sincronizar
      // agora reescreveria a URL com os valores default, descartando os filtros compartilhados por link.
      const fromQuery = this.$route.query.view
      this.viewMode = (fromQuery === 'list' || fromQuery === 'dashboard')
        ? fromQuery
        : (localStorage.getItem('portalcmj_pcl_view_mode') || this.viewMode)
      return this.viewMode
    },
    getResumoParams () {
      const f = this.filters_value
      const params = {}
      const situacao = (f.situacao || []).join(',')
      if (situacao) params.situacao = situacao
      if (f.unidade && typeof f.unidade === 'object') params.unidade = f.unidade.id
      if (f.entidade && typeof f.entidade === 'object') params.entidade = f.entidade.id
      if (f.parlamentares && typeof f.parlamentares === 'object') params.parlamentar = f.parlamentares.id
      if (f.search) params.search = f.search
      const tipos = _.filter(f.emendas_tipos, (v) => v)
      if (tipos.length) params.tipo__in = tipos.join(',')
      if (f.ajustes === 'True') params.ajustes = 'True'
      const extras = this.selected_loa_ids.filter(id => id !== this.loa.id)
      if (extras.length) params.loas = extras.join(',')
      return params
    },
    fetchResumo (fetchId) {
      const pedidos = [this.fetchConsulta('resumo', fetchId)]
      // o dashboard usa os mesmos filtros; fechado, fica para quando abrir
      this.dashboard = null
      if (this.viewMode === 'dashboard') pedidos.push(this.fetchDashboard(fetchId))
      return Promise.all(pedidos)
    },
    fetchDashboard (fetchId) {
      return this.fetchConsulta('dashboard', fetchId)
    },
    // Pede uma das consultas consolidadas e guarda a resposta em `this[nome]`.
    // A resposta de uma busca anterior é descartada.
    fetchConsulta (nome, fetchId) {
      return this.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: this.loa.id,
        action: `prestacaoconta_${nome}`,
        params: this.getResumoParams()
      }).then((response) => {
        if (this._fetchId !== fetchId) return
        this[nome] = response.data
      }).catch((error) => {
        if (this._fetchId !== fetchId) return
        this[nome] = null
        this.registrarFalha(error)
      })
    },
    // 404 é a resposta de quem não tem prestação de contas para consultar
    // (LOA sem norma, anterior ao ano inicial): não é falha, é lista vazia.
    registrarFalha (error) {
      const status = error && error.response && error.response.status
      if (status !== 404) this.erro = true
    },
    syncQueryString () {
      const query = { view: this.viewMode }
      this.filters.forEach((f) => {
        if (
          this.filters_value[f] !== null &&
          this.filters_value[f] !== undefined
        ) {
          const val = this.filters_value[f]
          if (Array.isArray(val)) {
            query[f] = val.join(',')
          } else if (typeof val === 'object' && val !== null) {
            query[f] = val.id
          } else {
            query[f] = val
          }
        }
      })
      // LOAs extras (exclui a pk_loa que já está na rota)
      const extraLoas = this.selected_loa_ids.filter(id => id !== this.loa.id)
      if (extraLoas.length) {
        query.loas = extraLoas.join(',')
      }
      this.$router.replace({ query }).catch(err => {
        if (err.name !== 'NavigationDuplicated') throw err
      })
    },
    applyUnidadeFilter (unidade) {
      if (this.selected_loa_ids.length > 1) return
      const uid = unidade && unidade.id
      if (!uid) return
      const unidadeSelect =
        this.$refs.filtros && this.$refs.filtros.getUnidadeSelectRef()
      if (unidadeSelect) {
        const opt = unidadeSelect.options.find(
          (o) => o.value && o.value.id === uid
        )
        if (opt) {
          this.filters_value = { ...this.filters_value, unidade: opt.value }
          return
        }
      }
      this.filters_value = { ...this.filters_value, unidade: unidade }
    },
    applyParlamentarFilter (parlamentar) {
      const pid = parlamentar && parlamentar.id
      if (!pid) return
      const opt = this.parlamentares_choice.find(
        (o) => o.value && o.value.id === pid
      )
      if (opt) {
        this.filters_value = { ...this.filters_value, parlamentares: opt.value }
      } else {
        this.filters_value = { ...this.filters_value, parlamentares: parlamentar }
      }
    },
    applyEntidadeFilter (entidade) {
      const eid = entidade && entidade.id
      if (!eid) return
      const entidadeSelect =
        this.$refs.filtros && this.$refs.filtros.getEntidadeSelectRef()
      if (entidadeSelect) {
        const opt = entidadeSelect.options.find(
          (o) => o.value && o.value.id === eid
        )
        if (opt) {
          this.filters_value = {
            ...this.filters_value,
            entidade: opt.value,
            emendas_tipos: ['10', '99'],
            ajustes: 'False'
          }
          return
        }
      }
      this.filters_value = {
        ...this.filters_value,
        entidade: entidade,
        emendas_tipos: ['10', '99'],
        ajustes: 'False'
      }
    },
    resetFilters () {
      this.currentPage = 1
      this.selected_loa_ids = [this.loa.id]
      this.filters_value = {
        unidade: null,
        entidade: null,
        parlamentares: null,
        situacao: [],
        emendas_tipos: [],
        ajustes: 'False',
        search: '',
        dash_activated: this.dash_activated
      }
    },
    onPageSizeChange (size) {
      this.pageSize = size
      this.currentPage = 1
      localStorage.setItem('portalcmj_page_size', size)
      this.fetchItens(this._fetchId)
    },
    onPageChange (page) {
      const totalPages = Math.max(1, Math.ceil(this.total_itens / this.pageSize))
      this.currentPage = Math.max(1, Math.min(page, totalPages))
      this.fetchItens(this._fetchId)
    },
    // Pede ao backend a página de cartões em exibição. Só a resposta do
    // pedido mais recente é usada: a de uma busca ou de uma página anterior
    // é descartada.
    fetchItens (fetchId) {
      const pedido = this._itensId = (this._itensId || 0) + 1
      this.fetching = true
      return this.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: this.loa.id,
        action: 'prestacaoconta_itens',
        params: {
          ...this.getResumoParams(),
          page: this.currentPage,
          page_size: this.pageSize
        }
      }).then((response) => {
        if (this._fetchId !== fetchId || this._itensId !== pedido) return
        this.itens = response.data.results.map(this.registroDoItem)
        this.total_itens = response.data.pagination.total_entries
      }).catch((error) => {
        if (this._fetchId !== fetchId || this._itensId !== pedido) return
        this.itens = []
        this.total_itens = 0
        this.registrarFalha(error)
      }).finally(() => {
        if (this._itensId === pedido) this.fetching = false
      })
    },
    // Item da consulta no formato que os cartões já usam. Os valores chegam
    // decididos pelo backend; aqui só se formata.
    registroDoItem (item) {
      const dinheiro = v => Number(v).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
      const parlamentares = item.parlamentares.map(p => ({
        id: p.id,
        __str__: p.nome,
        nome_parlamentar: p.nome,
        fotografia: p.fotografia,
        valor: p.valor
      }))
      const comum = {
        id: item.id,
        _loa_id: item.loa.id,
        loa: item.loa.id,
        __str__: item.titulo,
        link_detail_backend: item.link,
        tipo: item.tipo,
        fase: item.fase,
        fase_rotulo: item.fase_rotulo,
        unidade: item.unidade ? { id: item.unidade.id, __str__: item.unidade.nome } : null,
        valor_computado: Number(item.valor_final),
        str_valor_computado: dinheiro(item.valor_final),
        abas: item.abas
      }
      if (item.classe === 'emenda') {
        return {
          ...comum,
          __label__: 'loa_emendaloa',
          parlamentares,
          entidade: item.entidade
            ? { id: item.entidade.id, nome_fantasia: item.entidade.nome, __str__: item.entidade.nome }
            : null,
          materia: item.materia ? { id: item.materia } : null,
          epigrafe_short: item.titulo,
          str_valor: dinheiro(item.valor_original),
          has_ajustes: item.tem_ajustes,
          ementa_format: item.objeto
        }
      }
      const valor = Number(item.valor)
      return {
        ...comum,
        __label__: 'loa_registroajusteloa',
        parlamentares_valor: parlamentares,
        emendaloa: item.emendas.map(e => ({ id: e.id, __str__: e.titulo })),
        descricao: item.descricao,
        // valor negativo entre parênteses, como o cartão sempre mostrou
        str_valor: valor < 0 ? `(${dinheiro(-valor)})` : dinheiro(valor)
      }
    },

    on_loas_change (loaIds) {
      const prevIds = [...this.selected_loa_ids]
      this.selected_loa_ids = loaIds
      this.currentPage = 1

      const removedIds = prevIds.filter(id => !loaIds.includes(id))
      const addedIds = loaIds.filter(id => !prevIds.includes(id))

      if (!removedIds.length && !addedIds.length) return

      this.syncQueryString()

      // Opções dos seletores para a nova seleção e depois a busca
      return this.fetchOpcoes().then((descartou) => {
        // filtro descartado dispara o observador, que faz a busca completa
        if (descartou) return
        if (loaIds.length > 1 && this.filters_value.unidade) {
          // Limpar unidade dispara o watcher que faz fetch() completo
          this.filters_value = { ...this.filters_value, unidade: null }
          return
        }
        return this.fetch()
      })
    },

    // As opções do seletor chegam aos poucos: espera a do id pedido na URL
    // aparecer para aplicar o filtro. Desiste depois de 10 s (100 tentativas),
    // e o filtro da URL é descartado.
    aplicarFiltroQuandoHouverOpcao (filtro, id, select, tentativas = 100) {
      const opt = select.options.find((o) => o.value && o.value.id === id)
      if (opt) {
        this.filters_value[filtro] = opt.value
      } else if (tentativas > 1) {
        setTimeout(() => this.aplicarFiltroQuandoHouverOpcao(filtro, id, select, tentativas - 1), 100)
      }
    },
    applyQueryFilters () {
      const query = this.$route.query
      this.filters.forEach((f) => {
        if (query[f] !== undefined) {
          if (f === 'situacao') {
            this.filters_value[f] =
              typeof query[f] === 'string' ? query[f].split(',') : query[f]
          } else if (f === 'parlamentares') {
            const pid = parseInt(query[f])
            const opt = pid && this.parlamentares_choice.find((o) => o.value && o.value.id === pid)
            if (opt) this.filters_value[f] = opt.value
          } else if (f === 'emendas_tipos') {
            this.filters_value[f] =
              typeof query[f] === 'string' ? query[f].split(',') : query[f]
          } else if (f === 'unidade' || f === 'entidade') {
            const id = parseInt(query[f])
            if (id) {
              this.$nextTick(() => {
                const filtros = this.$refs.filtros
                const select = filtros && (f === 'unidade'
                  ? filtros.getUnidadeSelectRef()
                  : filtros.getEntidadeSelectRef())
                if (select) this.aplicarFiltroQuandoHouverOpcao(f, id, select)
              })
            }
          } else {
            this.filters_value[f] = query[f]
          }
        }
      })
    },

    // Uma busca: o resumo (e o dashboard, se aberto) e a página de cartões,
    // todos com os mesmos filtros. Nada da LOA é carregado inteiro.
    fetch () {
      if (!this.selected_loa_ids.length) return Promise.resolve()

      this._fetchId = (this._fetchId || 0) + 1
      const currentFetchId = this._fetchId

      this.firstPageLoaded = false
      this.erro = false
      this.itens = []
      this.total_itens = 0
      this.resumo = null

      return Promise.all([
        this.fetchResumo(currentFetchId),
        this.fetchItens(currentFetchId)
      ]).finally(() => {
        if (this._fetchId === currentFetchId) this.firstPageLoaded = true
      })
    },
    // Carga inicial: a LOA da rota e os exercícios disponíveis, depois a
    // primeira busca. A falha da LOA é avisada na tela.
    carregar () {
      const t = this
      t.erro = false
      const fetchLoa = t.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: t.loa.id,
        params: { include: 'id,ano' }
      })
      // os exercícios com prestação de contas para este usuário vêm do
      // backend, do mais recente para o mais antigo
      const fetchLoas = t.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: t.loa.id,
        action: 'prestacaoconta_resumo'
      }).then(resp => resp.data.exercicios).catch(() => [])
      return Promise.all([fetchLoa, fetchLoas]).then(([loaResp, exercicios]) => {
        t.loa = loaResp.data
        t.loas_list = exercicios.map(e => ({ id: e.id, ano: e.ano }))
        t.selected_loa_ids = [t.loa.id]

        // Restaura LOAs extras da query string
        const qsLoas = t.$route.query.loas
        if (qsLoas) {
          const validIds = t.loas_list.map(l => l.id)
          const extraIds = qsLoas.split(',').map(Number).filter(id => id && id !== t.loa.id && validIds.includes(id))
          if (extraIds.length) {
            t.selected_loa_ids = [t.loa.id, ...extraIds]
          }
        }

        // As opções dos seletores chegam antes da leitura dos filtros da URL
        return t.fetchOpcoes().then(() => {
          t.applyQueryFilters()
          t.ready = true
          // normaliza a querystring somente agora, com os filtros já lidos da url original
          t.syncQueryString()
          t.fetch()
        })
      }).catch(() => {
        t.erro = true
      })
    }
  },
  mounted () {
    this.viewModeRestore()
    this.removeAside()
    this.$nextTick().then(() => this.carregar())
  }
}
</script>
<style lang="scss" scoped>
.prestacaocontaloa-layout {
  .pcldetalhe-list {
    margin: 15px -15px 30px;
  }
}
</style>
