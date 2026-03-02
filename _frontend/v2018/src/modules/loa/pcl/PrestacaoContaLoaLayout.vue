<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <div class="row c-fields">
        <div class="col-md-3">
          Parlamentares
          <b-form-select @change="value => filters_value.parlamentares=value" v-model="filters_value.parlamentares" :options="parlamentares_choice" ></b-form-select>
        </div>
        <div class="col-md-4">
          Unidades Orçamentárias
          <model-select @change="value => filters_value.unidade=value"
            v-model="filters_value.unidade"
            app="loa"
            model="unidadeorcamentaria"
            choice="__str__"
            ordering="codigo"
            ref="unidadeSelect"
            :required="false"
            :extra_query="`${qs_loa}&recebe_emenda_impositiva=True`"
            ></model-select>
        </div>
        <div class="col-md-5">
          Filtre por termos nos Ajustes e Emendas Impositivas
          <b-form-input v-model="filters_value.search" placeholder="Digite um termo para pesquisa" class="mb-2"></b-form-input>
        </div>
        <div class="col-auto pt-2">
          Documentos
          <div class="d-flex">
            <b-form-checkbox class="ml-1" v-model="filters_value.emendas" value="True" unchecked-value="False">Emendas Impositivas</b-form-checkbox>
            <b-form-checkbox class="ml-4" v-model="filters_value.ajustes" value="True" unchecked-value="False">Registros de Ajustes</b-form-checkbox>
          </div>
        </div>
        <div class="col-auto pt-2">
          Situação
          <div class="d-flex">
            <b-form-checkbox-group v-model="filters_value.situacao">
              <b-form-checkbox class="ml-1" value="EM_TRAMITACAO">Aprovado: Em Tramitação</b-form-checkbox>
              <b-form-checkbox class="ml-4" value="FINALIZADO">Aprovado: Finalizado</b-form-checkbox>
              <b-form-checkbox class="ml-4" value="IMPEDIMENTO">Impedimento Técnico</b-form-checkbox>
            </b-form-checkbox-group>
          </div>
        </div>
      </div>
      <div class="row" v-if="results.ajustes || results.emendas">
        <div class="col-md-4 c-emendas-ajustes"><pre>{{ results }}</pre></div>
        <div class="col-md-8 c-prestacao-contas"></div>
      </div>
    </div>
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'

export default {
  name: 'prestacaocontaloa-layout',
  components: {
    ModelSelect
  },
  data () {
    return {
      loa: { id: this.$route.params.pkloa },
      ready: false,
      filters_value: {
        unidade: null,
        parlamentares: null,
        situacao: [],
        emendas: 'True',
        ajustes: 'True',
        search: ''
      },
      filters: [
        'unidade',
        'parlamentares',
        'situacao',
        'emendas',
        'ajustes',
        'search'
      ],
      results: {
        'emendas': {},
        'ajustes': {}
      },
      registro_selecionado: null,
      prestacaocontaregistro: null
    }
  },
  computed: {
    qs_loa: function () {
      const value = this.loa.id
      return value ? `&loa=${value}` : ''
    },
    parlamentares_choice: function () {
      if (this.loa.parlamentares && this.loa.parlamentares.length > 1) {
        return [{ value: null, text: '----------------' }, ...this.loa.parlamentares.map(p => ({ value: p, text: p.nome_parlamentar }))]
      }
      return this.loa.parlamentares ? this.loa.parlamentares.map(p => ({ value: p, text: p.nome_parlamentar })) : []
    }
  },
  watch: {
    filters_value: {
      deep: true,
      handler: function (nv, ov) {
        if (!this.ready) return
        // adicione todos os paramtros no histórico de rotas
        const query = {}
        this.filters.forEach(f => {
          if (this.filters_value[f] !== null && this.filters_value[f] !== undefined) {
            query[f] = this.filters_value[f]
          }
        })
        this.$router.replace({ query })
        this.fetch()
      }
    }
  },
  methods: {
    fetch_prestacaocontaregistro (registro) {
      this.registro_selecionado = registro
      const params = {
        [registro.__label__ === 'loa_emendaloa' ? 'emendaloa' : 'registro_ajuste']: registro.id,
        get_all: 'True' // parâmetro para retornar todos os registros sem paginação, visto que o número de registros é relativamente baixo
      }
      this.utils.fetch({
        app: 'loa',
        model: 'prestacaocontaregistro',
        params
      })
        .then((response) => {
          this.prestacaocontaregistro = response.data
        })
    },
    fetch () {
      this.results = {
        'emendas': {},
        'ajustes': {}
      }
      if ((this.filters_value.emendas === 'True') | (this.filters_value.ajustes === 'False' && this.filters_value.emendas === 'False')) {
        const params_emendas = {
          loa: this.loa.id,
          exclude: 'search'
        }
        if (this.filters_value.unidade && typeof this.filters_value.unidade === 'object') {
          params_emendas['unidade'] = this.filters_value.unidade.id
        }
        if (this.filters_value.parlamentares && typeof this.filters_value.parlamentares === 'object') {
          params_emendas['parlamentares'] = this.filters_value.parlamentares.id
        }
        if (this.filters_value.search) {
          params_emendas['search'] = this.filters_value.search
        }
        params_emendas['situacao'] = this.filters_value.situacao.join(',')
        params_emendas['get_all'] = 'True' // parâmetro para retornar todos os ajustes sem paginação, visto que o número de ajustes é relativamente baixo

        this.utils.fetch({
          app: 'loa',
          model: 'emendaloa',
          params: params_emendas
        })
          .then((response) => {
            this.results['emendas'] = response.data
          })
      }
      if ((this.filters_value.ajustes === 'True') | (this.filters_value.ajustes === 'False' && this.filters_value.emendas === 'False')) {
        const params_ajustes = {
          oficio_ajuste_loa__loa: this.loa.id,
          exclude: 'search'
        }
        if (this.filters_value.unidade && typeof this.filters_value.unidade === 'object') {
          params_ajustes['unidade'] = this.filters_value.unidade.id
        }
        if (this.filters_value.search) {
          params_ajustes['search'] = this.filters_value.search
        }
        params_ajustes['situacao'] = this.filters_value.situacao.join(',')
        params_ajustes['get_all'] = 'True' // parâmetro para retornar todos os ajustes sem paginação, visto que o número de ajustes é relativamente baixo
        this.utils.fetch({
          app: 'loa',
          model: 'registroajusteloa',
          params: params_ajustes
        })
          .then((response) => {
            this.results['ajustes'] = response.data
          })
      }
    }
  },
  mounted: function () {
    const t = this
    t.removeAside()
    const query = t.$route.query
    t.$nextTick()
      .then(() => {
        t.utils.fetch({
          app: 'loa',
          model: 'loa',
          id: t.loa.id,
          params: {
            expand: 'parlamentares'
          }
        })
          .then((response) => {
            t.loa = response.data
            // aplica parâmetros da query string nos filtros
            t.filters.forEach(f => {
              if (query[f] !== undefined) {
                if (f === 'situacao') {
                  t.filters_value[f] = typeof query[f] === 'string' ? query[f].split(',') : query[f]
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
