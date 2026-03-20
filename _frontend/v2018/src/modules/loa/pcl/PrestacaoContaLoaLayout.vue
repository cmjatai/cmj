<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <pcl-filtros
        ref="filtros"
        v-model="filters_value"
        :parlamentares-choice="parlamentares_choice"
        :qs-loa="qs_loa"
        @reset="resetFilters"
      />

      <div class="row mt-3" v-if="emendas_ajustes_list.length || fetching">
        <div class="col-md-4">
          <pcl-lista-emendas-ajustes
            :items="emendas_ajustes_list"
            :registro-selecionado="registro_selecionado"
            :fetching="fetching"
            @select="fetch_prestacaocontaregistro"
          />
        </div>
        <div class="col-md-8 pl-md-0">
          <pcl-detalhe-registro
            :registro="registro_selecionado"
            :prestacao-items="prestacaocontaregistro"
            :ajustes-items="ajustes_emendas_selecionados"
            :documentos-items="documentos_acessorios"
            :tramitacoes-items="tramitacoes"
          />
        </div>
      </div>
      <div v-else-if="ready" class="text-muted text-center py-5">
        Nenhum resultado encontrado para os filtros selecionados.
      </div>
    </div>
  </div>
</template>

<script>
import PclFiltros from './PclFiltros.vue'
import PclListaEmendasAjustes from './PclListaEmendasAjustes.vue'
import PclDetalheRegistro from './PclDetalheRegistro.vue'

export default {
  name: 'prestacaocontaloa-layout',
  components: {
    PclFiltros,
    PclListaEmendasAjustes,
    PclDetalheRegistro
  },
  data () {
    return {
      loa: { id: this.$route.params.pkloa },
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
      registro_selecionado: null,
      ajustes_emendas_selecionados: [],
      prestacaocontaregistro: null,
      documentos_acessorios: null,
      tramitacoes: null,
      fetching: false
    }
  },
  computed: {
    qs_loa () {
      const value = this.loa.id
      return value ? `&loa=${value}` : ''
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

    fetch_prestacaocontaregistro (registro) {
      this.registro_selecionado = registro
      this.prestacaocontaregistro = null
      this.ajustes_emendas_selecionados = null
      this.documentos_acessorios = null
      this.tramitacoes = null

      const params = {
        [registro.__label__ === 'loa_emendaloa' ? 'emendaloa' : 'registro_ajuste']: registro.id,
        get_all: 'True',
        expand: 'prestacao_conta'
      }
      this.utils
        .fetch({
          app: 'loa',
          model: 'prestacaocontaregistro',
          params
        })
        .then((response) => {
          this.prestacaocontaregistro = response.data
        })

      if (registro.__label__ === 'loa_emendaloa') {
        this.fetch_registroajusteloa(registro)
        if (registro.materia) {
          this.fetch_documentos_acessorios(registro)
          this.fetch_tramitacoes(registro)
        }
      }
    },

    fetch_registroajusteloa (registro) {
      const params = {
        emendaloa: registro.id,
        get_all: 'True',
        expand: 'oficio_ajuste_loa;unidade;materia'
      }
      this.utils
        .fetch({
          app: 'loa',
          model: 'registroajusteloa',
          params
        })
        .then((response) => {
          this.ajustes_emendas_selecionados = response.data
        })
    },

    fetch_documentos_acessorios (registro) {
      const materiaId =
        typeof registro.materia === 'object'
          ? registro.materia.id
          : registro.materia
      const params = {
        materia: materiaId,
        get_all: 'True',
        expand: 'tipo'
      }
      this.utils
        .fetch({
          app: 'materia',
          model: 'documentoacessorio',
          params
        })
        .then((response) => {
          this.documentos_acessorios = response.data
        })
    },

    fetch_tramitacoes (registro) {
      const materiaId =
        typeof registro.materia === 'object'
          ? registro.materia.id
          : registro.materia
      const params = {
        materia: materiaId,
        get_all: 'True',
        expand: 'unidade_tramitacao_destino;status',
        include: 'status.id,__str__;unidade_tramitacao_destino.id,__str__'

      }
      this.utils
        .fetch({
          app: 'materia',
          model: 'tramitacao',
          params
        })
        .then((response) => {
          this.tramitacoes = response.data
        })
    },

    fetch () {
      this.registro_selecionado = null
      this.prestacaocontaregistro = null
      this.ajustes_emendas_selecionados = null
      this.documentos_acessorios = null
      this.tramitacoes = null
      this.fetching = true

      const promises = {}
      const emendasTipos = this.filters_value.emendas_tipos
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
          this.$nextTick(() => {
            if (this.emendas_ajustes_list.length > 0) {
              this.fetch_prestacaocontaregistro(this.emendas_ajustes_list[0])
            }
          })
        })
        .finally(() => {
          this.fetching = false
        })
    }
  },
  mounted () {
    const t = this
    t.removeAside()
    const query = t.$route.query
    t.$nextTick().then(() => {
      t.utils
        .fetch({
          app: 'loa',
          model: 'loa',
          id: t.loa.id,
          params: {
            expand: 'parlamentares',
            include: 'parlamentares.id,nome_parlamentar'

          }
        })
        .then((response) => {
          t.loa = response.data
          // aplica parâmetros da query string nos filtros
          t.filters.forEach((f) => {
            if (query[f] !== undefined) {
              if (f === 'situacao') {
                t.filters_value[f] =
                  typeof query[f] === 'string' ? query[f].split(',') : query[f]
              } else if (f === 'parlamentares') {
                const pid = parseInt(query[f])
                if (pid && t.loa.parlamentares) {
                  const found = t.loa.parlamentares.find((p) => p.id === pid)
                  if (found) {
                    t.filters_value[f] = found
                  }
                }
              } else if (f === 'emendas_tipos') {
                t.filters_value[f] =
                  typeof query[f] === 'string' ? query[f].split(',') : query[f]
              } else if (f === 'unidade') {
                const uid = parseInt(query[f])
                if (uid) {
                  t.$nextTick(() => {
                    const unidadeSelect =
                      t.$refs.filtros && t.$refs.filtros.getUnidadeSelectRef()
                    if (unidadeSelect) {
                      const checkOptions = () => {
                        const opt = unidadeSelect.options.find(
                          (o) => o.value && o.value.id === uid
                        )
                        if (opt) {
                          t.filters_value.unidade = opt.value
                        } else {
                          setTimeout(checkOptions, 100)
                        }
                      }
                      checkOptions()
                    }
                  })
                }
              } else {
                t.filters_value[f] = query[f]
              }
            }
          })
          t.ready = true
          t.fetch()
        })
    })
  }
}
</script>
