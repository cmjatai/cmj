<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div class="container" v-if="loa.ano">
      <div class="row c-fields">
        <div class="col-md-3">
          Parlamentares
          <b-form-select @change="value => despesa.parlamentares_selected=value" v-model="despesa.parlamentares_selected" :options="parlamentares_choice" ></b-form-select>
        </div>
        <div class="col-md-3">
          Unidades Orçamentárias
          <model-select @change="value => despesa.unidade_selected=value"
            v-model="despesa.unidade_selected"
            app="loa"
            model="unidadeorcamentaria"
            choice="__str__"
            ordering="codigo"
            ref="unidadeSelect"
            :required="false"
            :extra_query="`${qs_loa}&recebe_emenda_impositiva=True`"
            ></model-select>
        </div>
        <div class="col-md-6">
          Filtre por termos nos Ajustes e Emendas Impositivas
          <b-form-input v-model="despesa.termo_search" placeholder="Digite um termo para pesquisa" class="mb-2"></b-form-input>
        </div>
        <div class="col-auto pt-2">
          Situação
          <div class="d-flex">
            <b-form-checkbox class="m-2" v-model="despesa.emtramitacao_selected" value="True" unchecked-value="False">Em Tramitação</b-form-checkbox>
            <b-form-checkbox class="m-2" v-model="despesa.finalizada_selected" value="True" unchecked-value="False">Finalizado</b-form-checkbox>
            <b-form-checkbox class="m-2" v-model="despesa.impedimento_selected" value="True" unchecked-value="False">Impedimento Técnico</b-form-checkbox>
          </div>
        </div>
        <div class="col-auto pt-2">
          Documentos
          <div class="d-flex">
            <b-form-checkbox class="m-2" v-model="despesa.emendas_selected" value="True" unchecked-value="False">Emendas Impositivas</b-form-checkbox>
            <b-form-checkbox class="m-2" v-model="despesa.oficios_selected" value="True" unchecked-value="False">Registros de Ajustes</b-form-checkbox>
          </div>
        </div>
      </div>
    </div>
    <div class="container-table" v-if="results">
      <p>Exibir tabela de despesas aqui</p>
      <pre>{{ results }}</pre>
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
      despesa: {
        unidade_selected: null,
        parlamentares_selected: null,
        emtramitacao_selected: 'False',
        finalizada_selected: 'False',
        impedimento_selected: 'False',
        emendas_selected: 'False',
        oficios_selected: 'False',
        termo_search: ''
      },
      filters: [
        'unidade_selected',
        'parlamentares_selected',
        'emtramitacao_selected',
        'finalizada_selected',
        'impedimento_selected',
        'emendas_selected',
        'oficios_selected',
        'termo_search'
      ],
      results: null
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
    despesa: {
      deep: true,
      immediate: true,
      handler: function (nv, ov) {
        this.fetch()
      }
    }
  },
  methods: {
    fetch () {
      this.results = 'response.data'
      const params = {}
      this.filters.forEach(filter => {
        if (this.despesa[filter] !== null) {
          // se this.despesa[filter] for um objeto, passa o id, senão passa o valor diretamente
          params[filter.replace('_selected', '')] = typeof this.despesa[filter] === 'object' ? this.despesa[filter].id : this.despesa[filter]
        }
      })
      params['prestacao_conta__loa'] = this.loa.id
      params['expand'] = 'emendaloa;registro_ajuste;prestacao_conta'
      this.utils.fetch({
        app: 'loa',
        model: 'prestacaocontaregistro',
        params: params
      })
        .then((response) => {
          this.results = response.data
        })
    }
  },
  mounted: function () {
    const t = this
    t.removeAside()
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
          })
      })
  }
}
</script>
