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
      <div class="row mt-3" v-if="emendas_ajustes_list.length">
        <div class="col-md-5 c-emendas-ajustes">
          <h6>Emendas e Ajustes <small class="text-muted">({{ emendas_ajustes_list.length }})</small></h6>
          <div class="list-group">
            <a href="#"
              v-for="item in emendas_ajustes_list"
              :key="`${item.__label__}_${item.id}`"
              class="list-group-item list-group-item-action py-2"
              :class="{ active: registro_selecionado && registro_selecionado.id === item.id && registro_selecionado.__label__ === item.__label__ }"
              @click.prevent="fetch_prestacaocontaregistro(item)"
            >
              <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1 mr-2">
                  <b-badge :variant="item.__label__ === 'loa_emendaloa' ? 'primary' : 'warning'" class="mr-1">
                    {{ item.__label__ === 'loa_emendaloa' ? 'Emenda' : 'Ajuste' }}
                  </b-badge>
                  <b-badge v-if="item.__label__ === 'loa_emendaloa'" :variant="fase_variant(item.fase)" class="mr-1">
                    {{ fase_label(item.fase) }}
                  </b-badge>
                  <div class="mt-1 small">{{ item.__str__ }}</div>
                </div>
              </div>
            </a>
          </div>
        </div>
        <div class="col-md-7 c-prestacao-contas">
          <template v-if="registro_selecionado">
            <h6>
              Prestação de Contas:
              <b-badge :variant="registro_selecionado.__label__ === 'loa_emendaloa' ? 'primary' : 'warning'">
                {{ registro_selecionado.__label__ === 'loa_emendaloa' ? 'Emenda' : 'Ajuste' }}
              </b-badge>
            </h6>
            
            <p class="small text-muted mb-2">{{ registro_selecionado.__str__ }}</p>

            <div v-if="prestacaocontaregistro === null" class="text-center py-3">
              <b-spinner small></b-spinner> Carregando...
            </div>
            <div v-else-if="prestacaocontaregistro.length === 0" class="text-muted text-center py-3">
              Nenhum registro de prestação de contas encontrado.
            </div>
            <b-table v-else
              :items="prestacaocontaregistro"
              :fields="prestacao_fields"
              small striped hover
              class="mb-0"
            >
              <template #cell(situacao)="data">
                <b-badge :variant="situacao_variant(data.value)">{{ situacao_label(data.value) }}</b-badge>
              </template>
              <template #cell(detalhamento)="data">
                <span class="small">{{ data.value || '—' }}</span>
              </template>
              <template #cell(prestacao_conta)="data">
                <span class="small">{{ data.item.prestacao_conta__str__ || data.value }}</span>
              </template>
            </b-table>
            <pre>{{ registro_selecionado }}</pre>
          </template>
          <div v-else class="text-muted text-center py-5">
            Selecione uma emenda ou ajuste para ver os registros de prestação de contas.
          </div>
        </div>
      </div>
      <div v-else-if="ready" class="text-muted text-center py-5">
        Nenhum resultado encontrado para os filtros selecionados.
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
    },
    emendas_ajustes_list: function () {
      const emendas = Array.isArray(this.results.emendas) ? this.results.emendas : []
      const ajustes = Array.isArray(this.results.ajustes) ? this.results.ajustes : []
      return [...emendas, ...ajustes]
    },
    prestacao_fields: function () {
      return [
        { key: 'situacao', label: 'Situação', sortable: true },
        { key: 'detalhamento', label: 'Detalhamento' },
        { key: 'prestacao_conta', label: 'Prestação de Conta' }
      ]
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
    fase_variant (fase) {
      const map = { 30: 'success', 40: 'danger', 50: 'info', 20: 'secondary' }
      return map[fase] || 'light'
    },
    fase_label (fase) {
      const map = {
        10: 'Proposta',
        12: 'Proposta Liberada',
        15: 'Edição Contábil',
        17: 'Liberado Contab.',
        20: 'Em Tramitação',
        25: 'Aprov. Legislativa',
        30: 'Aprovada',
        40: 'Impedimento',
        50: 'Imped. Sanado'
      }
      return map[fase] || `Fase ${fase}`
    },
    situacao_variant (situacao) {
      const map = { EM_TRAMITACAO: 'info', FINALIZADO: 'success', OUTRO: 'secondary' }
      return map[situacao] || 'light'
    },
    situacao_label (situacao) {
      const map = { EM_TRAMITACAO: 'Em Tramitação', FINALIZADO: 'Finalizado', OUTRO: 'Outros' }
      return map[situacao] || situacao
    },
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
      this.registro_selecionado = null
      this.prestacaocontaregistro = null
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
