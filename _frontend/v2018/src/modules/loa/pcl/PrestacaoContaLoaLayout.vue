<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <pcl-filtros
        ref="filtros"
        :disabled="!ready || !firstPageLoaded"
        v-model="filters_value"
        :parlamentares-choice="parlamentares_choice"
        :qs-loa="qs_loa"
        :qs-emenda-loa="qs_emenda_loa__loa"
        :loas-choice="loas_choice"
        :selected-loa-ids="selected_loa_ids"
        :locked-loa-id="loa.id"
        :total-items="emendas_ajustes_list.length"
        :page-size="pageSize"
        :current-page="currentPage"
        :fetching="fetching"
        @update:page-size="onPageSizeChange"
        @update:current-page="onPageChange"
        @reset="resetFilters"
        @loas-change="on_loas_change"
      />

      <pcl-totalizacao
        v-if="emendas_ajustes_list.length"
        :lista="emendas_ajustes_list"
        :parlamentar-selecionado="filters_value.parlamentares"
        class="mt-3"
      />

      <div class="pcldetalhe-list" v-if="emendas_ajustes_list.length || fetching">
        <template v-for="item in paginatedList">
          <pcl-detalhe-emenda
            v-if="item.__label__ === 'loa_emendaloa'"
            :key="`emenda_${item.id}`"
            :registro="item"
            :unidade-filter-disabled="selected_loa_ids.length > 1"
            @filter-unidade="applyUnidadeFilter"
            @filter-entidade="applyEntidadeFilter"
            @filter-parlamentar="applyParlamentarFilter"
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
      <div v-else-if="ready" class="card text-muted text-center my-3 p-3 mx-5 font-weight-bold">
        Nenhum resultado encontrado para os filtros selecionados.
      </div>
    </div>
  </div>
</template>

<script>
import PclFiltros from './PclFiltros.vue'
import PclDetalheEmenda from './PclDetalheEmenda.vue'
import PclDetalheAjuste from './PclDetalheAjuste.vue'
import PclTotalizacao from './PclTotalizacao.vue'

export default {
  name: 'prestacaocontaloa-layout',
  components: {
    PclFiltros,
    PclDetalheEmenda,
    PclDetalheAjuste,
    PclTotalizacao
  },
  data () {
    return {
      loa: { id: this.$route.params.pkloa },
      loas_list: [],
      selected_loa_ids: [],
      loas_data: {},
      ready: false,
      filters_value: {
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
      results: {
        emendas: [],
        ajustes: []
      },
      fetching: false,
      firstPageLoaded: false,
      currentPage: 1,
      pageSize: Number(localStorage.getItem('portalcmj_page_size')) || 10
    }
  },
  computed: {
    qs_loa () {
      if (this.selected_loa_ids.length === 1) return `loa=${this.selected_loa_ids[0]}`
      return ''
    },
    qs_emenda_loa__loa () {
      if (this.selected_loa_ids.length === 1) return `&emendaloa_set__loa=${this.selected_loa_ids[0]}`
      return ''
    },
    loas_choice () {
      if (!this.loas_list.length) return []
      return this.loas_list.map(l => ({
        value: l.id,
        text: l.ano
      }))
    },
    all_parlamentares () {
      const map = {}
      this.selected_loa_ids.forEach(id => {
        const loaData = this.loas_data[id]
        if (loaData && loaData.parlamentares) {
          loaData.parlamentares.forEach(p => {
            if (!map[p.id]) map[p.id] = p
          })
        }
      })
      return Object.values(map).sort((a, b) =>
        (a.nome_parlamentar || '').localeCompare(b.nome_parlamentar || '')
      )
    },
    parlamentares_choice () {
      if (this.all_parlamentares.length > 1) {
        return [
          { value: null, text: '----------------' },
          ...this.all_parlamentares.map((p) => ({
            value: p,
            text: p.nome_parlamentar
          }))
        ]
      }
      return this.all_parlamentares.map((p) => ({
        value: p,
        text: p.nome_parlamentar
      }))
    },
    emendas_ajustes_list () {
      const emendas = Array.isArray(this.results.emendas)
        ? this.results.emendas
        : []
      const ajustes = Array.isArray(this.results.ajustes)
        ? this.results.ajustes
        : []
      return [...emendas, ...ajustes]
    },
    paginatedList () {
      const start = (this.currentPage - 1) * this.pageSize
      return this.emendas_ajustes_list.slice(start, start + this.pageSize)
    }
  },
  watch: {
    filters_value: {
      deep: true,
      handler (nv, ov) {
        if (!this.ready) return
        this.currentPage = 1
        // sincroniza parâmetros com o histórico de rotas
        const query = {}
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
        this.$router.replace({ query }).catch(err => {
          if (err.name !== 'NavigationDuplicated') throw err
        })
        this.fetch()
      }
    }
  },
  methods: {
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
        search: ''
      }
    },
    onPageSizeChange (size) {
      this.pageSize = size
      this.currentPage = 1
      localStorage.setItem('portalcmj_page_size', size)
    },
    onPageChange (page) {
      const totalPages = Math.max(1, Math.ceil(this.emendas_ajustes_list.length / this.pageSize))
      this.currentPage = Math.max(1, Math.min(page, totalPages))
    },

    on_loas_change (loaIds) {
      this.selected_loa_ids = loaIds
      if (loaIds.length > 1 && this.filters_value.unidade) {
        this.filters_value = { ...this.filters_value, unidade: null }
      }
      const newIds = loaIds.filter(id => !this.loas_data[id])
      if (newIds.length) {
        Promise.all(newIds.map(id =>
          this.utils.fetch({
            app: 'loa',
            model: 'loa',
            id,
            params: {
              expand: 'parlamentares',
              include: 'parlamentares.id,nome_parlamentar'
            }
          }).then(resp => {
            this.$set(this.loas_data, id, resp.data)
          })
        )).then(() => {
          this.currentPage = 1
          this.fetch()
        })
      } else {
        this.currentPage = 1
        this.fetch()
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
            if (pid && this.loa.parlamentares) {
              const found = this.loa.parlamentares.find((p) => p.id === pid)
              if (found) {
                this.filters_value[f] = found
              }
            }
          } else if (f === 'emendas_tipos') {
            this.filters_value[f] =
              typeof query[f] === 'string' ? query[f].split(',') : query[f]
          } else if (f === 'unidade') {
            const uid = parseInt(query[f])
            if (uid) {
              this.$nextTick(() => {
                const unidadeSelect =
                  this.$refs.filtros && this.$refs.filtros.getUnidadeSelectRef()
                if (unidadeSelect) {
                  const checkOptions = () => {
                    const opt = unidadeSelect.options.find(
                      (o) => o.value && o.value.id === uid
                    )
                    if (opt) {
                      this.filters_value.unidade = opt.value
                    } else {
                      setTimeout(checkOptions, 100)
                    }
                  }
                  checkOptions()
                }
              })
            }
          } else {
            this.filters_value[f] = query[f]
          }
        }
      })
    },

    _fetchAllPages (resultKey, model, params, fetchId) {
      const fetchPage = (page) => {
        if (this._fetchId !== fetchId) return Promise.resolve()

        return this.utils.fetch({
          app: 'loa',
          model: model,
          params: { ...params, page }
        }).then((response) => {
          if (this._fetchId !== fetchId) return

          const data = response.data
          let items = []
          let nextPage = null

          if (data && data.pagination && Array.isArray(data.results)) {
            items = data.results
            nextPage = data.pagination.next_page
          } else if (Array.isArray(data)) {
            items = data
          }

          if (items.length) {
            this.results = Object.assign({}, this.results, {
              [resultKey]: [...this.results[resultKey], ...items]
            })
            this.firstPageLoaded = true
          }

          if (nextPage) {
            return fetchPage(nextPage)
          }
        })
      }
      return fetchPage(1)
    },

    fetch () {
      if (!this.selected_loa_ids.length) return Promise.resolve()

      this._fetchId = (this._fetchId || 0) + 1
      const currentFetchId = this._fetchId

      this.fetching = true
      this.firstPageLoaded = false
      this.results = { emendas: [], ajustes: [] }

      const emendasTipos = _.filter(this.filters_value.emendas_tipos, (v) => v)
      const fetchEmendas =
        (Array.isArray(emendasTipos) && emendasTipos.length > 0) ||
        (this.filters_value.ajustes === 'False' &&
          (!Array.isArray(emendasTipos) || emendasTipos.length === 0))
      const fetchAjustes =
        (this.filters_value.ajustes === 'True') ||
        (this.filters_value.ajustes === 'False' &&
          (!Array.isArray(emendasTipos) || emendasTipos.length === 0))

      const pending = []

      this.selected_loa_ids.forEach(loaId => {
        if (fetchEmendas) {
          const params_emendas = {
            loa: loaId,
            o: 'materia__tipo__sigla,materia__numero',
            exclude: 'search;metadata',
            include: 'parlamentares.id,__str__,fotografia;unidade.id,__str__;materia.id',
            expand: 'parlamentares;unidade;materia;entidade',
            page_size: 20,
            situacao: this.filters_value.situacao.join(',')
          }
          if (
            this.filters_value.unidade &&
            typeof this.filters_value.unidade === 'object'
          ) {
            params_emendas.unidade = this.filters_value.unidade.id
          }
          if (
            this.filters_value.entidade &&
            typeof this.filters_value.entidade === 'object'
          ) {
            params_emendas.entidade = this.filters_value.entidade.id
          }
          if (
            this.filters_value.parlamentares &&
            typeof this.filters_value.parlamentares === 'object'
          ) {
            params_emendas.parlamentares = this.filters_value.parlamentares.id
          }
          if (this.filters_value.search) {
            params_emendas.search = this.filters_value.search
          }
          if (Array.isArray(emendasTipos) && emendasTipos.length > 0) {
            params_emendas.tipo__in = emendasTipos.join(',')
          }
          pending.push(this._fetchAllPages('emendas', 'emendaloa', params_emendas, currentFetchId))
        }

        if (fetchAjustes) {
          const params_ajustes = {
            oficio_ajuste_loa__loa: loaId,
            exclude: 'search',
            include: 'parlamentares_valor.id,__str__,fotografia;oficio_ajuste_loa.id,__str__',
            expand: 'emendaloa.id,__str__;unidade;parlamentares_valor;oficio_ajuste_loa',
            o: 'parlamentares_valor__nome_parlamentar',
            page_size: 20
          }
          if (
            this.filters_value.unidade &&
            typeof this.filters_value.unidade === 'object'
          ) {
            params_ajustes.unidade = this.filters_value.unidade.id
          }
          if (
            this.filters_value.entidade &&
            typeof this.filters_value.entidade === 'object'
          ) {
            params_ajustes.entidade = this.filters_value.entidade.id
          }

          if (this.filters_value.search) {
            params_ajustes.search = this.filters_value.search
          }
          if (
            this.filters_value.parlamentares &&
            typeof this.filters_value.parlamentares === 'object'
          ) {
            params_ajustes.parlamentares_valor =
              this.filters_value.parlamentares.id
          }
          params_ajustes.situacao = this.filters_value.situacao.join(',')

          pending.push(this._fetchAllPages('ajustes', 'registroajusteloa', params_ajustes, currentFetchId))
        }
      })

      if (!pending.length) {
        this.fetching = false
        this.firstPageLoaded = true
        return Promise.resolve()
      }

      return Promise.all(pending).finally(() => {
        if (this._fetchId === currentFetchId) {
          this.fetching = false
          this.firstPageLoaded = true
        }
      })
    }
  },
  mounted () {
    const t = this
    t.removeAside()
    t.$nextTick().then(() => {
      const fetchLoa = t.utils.fetch({
        app: 'loa',
        model: 'loa',
        id: t.loa.id,
        params: {
          expand: 'parlamentares',
          include: 'parlamentares.id,nome_parlamentar'
        }
      })
      const fetchLoas = t.utils.fetch({
        app: 'loa',
        model: 'loa',
        params: {
          ano__gte: 2023,
          get_all: 'True',
          o: '-ano'
        }
      })
      Promise.all([fetchLoa, fetchLoas]).then(([loaResp, loasResp]) => {
        t.loa = loaResp.data
        t.loas_list = loasResp.data
        t.loas_data = { [t.loa.id]: t.loa }
        t.selected_loa_ids = [t.loa.id]
        t.applyQueryFilters()
        t.ready = true
        t.fetch()
      })
    })
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
