<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <pcl-filtros
        ref="filtros"
        :disabled="!ready || fetching"
        v-model="filters_value"
        :parlamentares-choice="parlamentares_choice"
        :qs-loa="qs_loa"
        :loas-choice="loas_choice"
        :loa-value="loa"
        @reset="resetFilters"
        @loa-change="on_loa_change"
      />

      <pcl-totalizacao
        v-if="!fetching && emendas_ajustes_list.length"
        :lista="emendas_ajustes_list"
        class="mt-3"
      />

      <div class="mt-3" v-if="emendas_ajustes_list.length || fetching">
        <b-spinner v-if="fetching" small variant="secondary" class="d-block mx-auto my-3"></b-spinner>
        <template v-for="item in emendas_ajustes_list">
          <pcl-detalhe-emenda
            v-if="item.__label__ === 'loa_emendaloa'"
            :key="`emenda_${item.id}`"
            :registro="item"
          />
          <pcl-detalhe-ajuste
            v-else
            :key="`ajuste_${item.id}`"
            :registro="item"
          />
        </template>
      </div>
      <div v-else-if="ready" class="text-muted text-center py-5">
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
      ready: false,
      filters_value: {
        unidade: null,
        parlamentares: null,
        situacao: [],
        emendas_tipos: ['0', '10', '99'],
        ajustes: 'True',
        search: ''
      },
      filters: [
        'unidade',
        'parlamentares',
        'situacao',
        'emendas_tipos',
        'ajustes',
        'search'
      ],
      results: {
        emendas: {},
        ajustes: {}
      },
      fetching: false
    }
  },
  computed: {
    qs_loa () {
      const value = this.loa.id
      return value ? `&loa=${value}` : ''
    },
    loas_choice () {
      if (!this.loas_list.length) return []
      return this.loas_list.map(l => ({
        value: l.id,
        text: `LOA ${l.ano}`
      }))
    },
    parlamentares_choice () {
      if (this.loa.parlamentares && this.loa.parlamentares.length > 1) {
        return [
          { value: null, text: '----------------' },
          ...this.loa.parlamentares.map((p) => ({
            value: p,
            text: p.nome_parlamentar
          }))
        ]
      }
      return this.loa.parlamentares
        ? this.loa.parlamentares.map((p) => ({
          value: p,
          text: p.nome_parlamentar
        }))
        : []
    },
    emendas_ajustes_list () {
      const emendas = Array.isArray(this.results.emendas)
        ? this.results.emendas
        : []
      const ajustes = Array.isArray(this.results.ajustes)
        ? this.results.ajustes
        : []
      return [...emendas, ...ajustes]
    }
  },
  watch: {
    filters_value: {
      deep: true,
      handler (nv, ov) {
        if (!this.ready) return
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
        this.$router.replace({ query })
        this.fetch()
      }
    }
  },
  methods: {
    resetFilters () {
      this.filters_value = {
        unidade: null,
        parlamentares: null,
        situacao: [],
        emendas_tipos: ['0', '10', '99'],
        ajustes: 'True',
        search: ''
      }
    },

    on_loa_change (loaId) {
      if (!loaId || loaId === this.loa.id) return
      const query = {}
      this.filters.forEach((f) => {
        if (f === 'unidade') return
        const val = this.filters_value[f]
        if (val === null || val === undefined) return
        if (Array.isArray(val)) {
          query[f] = val.join(',')
        } else if (typeof val === 'object') {
          query[f] = val.id
        } else {
          query[f] = val
        }
      })
      const resolved = this.$router.resolve({
        name: this.$route.name,
        params: { ...this.$route.params, pkloa: loaId },
        query
      })
      window.location.href = resolved.href
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

    fetch () {
      if (!this.loa.id) return Promise.resolve()
      this.fetching = true

      const promises = {}
      const emendasTipos = _.filter(this.filters_value.emendas_tipos, (v) => v)
      const fetchEmendas =
        (Array.isArray(emendasTipos) && emendasTipos.length > 0) ||
        (this.filters_value.ajustes === 'False' &&
          (!Array.isArray(emendasTipos) || emendasTipos.length === 0))
      const fetchAjustes =
        (this.filters_value.ajustes === 'True') ||
        (this.filters_value.ajustes === 'False' &&
          (!Array.isArray(emendasTipos) || emendasTipos.length === 0))

      if (fetchEmendas) {
        const params_emendas = {
          loa: this.loa.id,
          o: '-tipo,fase,materia__tipo__sigla,materia__numero',
          exclude: 'search;metadata',
          include: 'parlamentares.id,__str__,fotografia;unidade.id,__str__;materia.id',
          expand: 'parlamentares;unidade;materia;entidade',
          get_all: 'True',
          situacao: this.filters_value.situacao.join(',')
        }
        if (
          this.filters_value.unidade &&
          typeof this.filters_value.unidade === 'object'
        ) {
          params_emendas.unidade = this.filters_value.unidade.id
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
        promises.emendas = this.utils.fetch({
          app: 'loa',
          model: 'emendaloa',
          params: params_emendas
        })
      }

      if (fetchAjustes) {
        const params_ajustes = {
          oficio_ajuste_loa__loa: this.loa.id,
          exclude: 'search',
          expand: 'emendaloa.id,__str__;unidade',
          o: 'parlamentares_valor__nome_parlamentar'
        }
        if (
          this.filters_value.unidade &&
          typeof this.filters_value.unidade === 'object'
        ) {
          params_ajustes.unidade = this.filters_value.unidade.id
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
        params_ajustes.get_all = 'True'

        promises.ajustes = this.utils.fetch({
          app: 'loa',
          model: 'registroajusteloa',
          params: params_ajustes
        })
      }

      const keys = Object.keys(promises)
      return Promise.all(Object.values(promises))
        .then((responses) => {
          const newResults = { emendas: {}, ajustes: {} }
          keys.forEach((key, i) => {
            newResults[key] = responses[i].data
          })
          this.results = newResults
        })
        .finally(() => {
          this.fetching = false
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
          get_all: 'True',
          o: '-ano'
        }
      })
      Promise.all([fetchLoa, fetchLoas]).then(([loaResp, loasResp]) => {
        t.loa = loaResp.data
        t.loas_list = loasResp.data
        t.applyQueryFilters()
        t.ready = true
        t.fetch()
      })
    })
  }
}
</script>
