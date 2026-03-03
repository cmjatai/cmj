<template>
  <div class="prestacaocontaloa-layout pt-3">
    <div v-if="loa.ano">
      <div class="c-fields card card-body bg-light py-3 px-3 mb-0">
        <div class="row">
          <div class="col-md-5 mb-2">
            <label class="c-fields-label">Pesquisa</label>
            <b-form-input :value="filters_value.search" @change="value => filters_value.search = value" placeholder="Filtre por termos nos Ajustes e Emendas" size="sm"></b-form-input>
          </div>
          <div class="col-md-3 mb-2">
            <label class="c-fields-label">Parlamentares</label>
            <b-form-select @change="value => filters_value.parlamentares=value" v-model="filters_value.parlamentares" :options="parlamentares_choice" size="sm"></b-form-select>
          </div>
          <div class="col-md-4 mb-2">
            <label class="c-fields-label">Unidade Orçamentária</label>
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
          <div class="col-12 text-muted small mb-0">
            OBS: A não seleção de todos os filtros de cada categoria retorna todos os registros relacionados à LOA.
          </div>
        </div>
        <div class="row align-items-end mt-2">
          <div class="col-auto">
            <label class="c-fields-label">Documentos</label>
            <div class="c-fields-check-group d-flex">
              <b-form-checkbox class="mr-3" v-model="filters_value.emendas" value="True" unchecked-value="False">Emendas Impositivas</b-form-checkbox>
              <b-form-checkbox v-model="filters_value.ajustes" value="True" unchecked-value="False">Registros de Ajustes</b-form-checkbox>
            </div>
          </div>
          <div class="col-auto">
            <label class="c-fields-label">Situação</label>
            <div class="c-fields-check-group d-flex">
              <b-form-checkbox-group v-model="filters_value.situacao">
                <b-form-checkbox class="mr-3" value="EM_TRAMITACAO">Em Tramitação</b-form-checkbox>
                <b-form-checkbox class="mr-3" value="FINALIZADO">Finalizado</b-form-checkbox>
                <b-form-checkbox value="IMPEDIMENTO">Impedimento Técnico</b-form-checkbox>
              </b-form-checkbox-group>
            </div>
          </div>
          <div class="col-auto ml-auto">
            <button class="btn btn-sm btn-outline-secondary" @click="resetFilters" title="Limpar todos os filtros">
              <i class="fas fa-times mr-1"></i>Limpar
            </button>
          </div>
        </div>
      </div>
      <div class="row mt-3" v-if="emendas_ajustes_list.length || fetching">
        <div class="col-md-4 c-emendas-ajustes">
          <h6 class="c-emendas-ajustes-header">Emendas e Ajustes <small class="text-muted">({{ emendas_ajustes_list.length }})</small> <b-spinner v-if="fetching" small variant="secondary" class="ml-1"></b-spinner></h6>
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
        <div class="col-md-8 c-prestacao-contas pl-md-0">
          <template v-if="registro_selecionado">
            <div class="card mb-3">
              <div class="card-header d-flex align-items-center justify-content-between py-2">
                <div>
                  <b-badge :variant="registro_selecionado.__label__ === 'loa_emendaloa' ? 'primary' : 'warning'" class="mr-2">
                    {{ registro_selecionado.__label__ === 'loa_emendaloa' ? 'Emenda Impositiva' : 'Registro de Ajuste' }}
                  </b-badge>
                  <span class="font-weight-bold">Prestação de Contas</span>
                </div>
                <a :href="registro_selecionado.link_detail_backend"
                  target="_blank"
                  class="btn btn-sm btn-outline-secondary"
                  title="Abrir detalhes no painel administrativo"
                >
                  <i class="fas fa-external-link-alt mr-1"></i> Abrir
                </a>
              </div>
              <div class="card-body py-2">
                <p class="mb-2" v-if="registro_selecionado.__label__ === 'loa_emendaloa'">
                  {{ registro_selecionado.__str__ }}
                </p>
                <p class="mb-2" v-else>
                  {{ registro_selecionado.descricao }}
                </p>
                <div class="row small text-muted mt-1" v-if="registro_selecionado.unidade || (registro_selecionado.parlamentares && registro_selecionado.parlamentares.length)">
                  <div class="col-12" v-if="registro_selecionado.unidade">
                    <i class="fas fa-building mr-1"></i>
                    <strong>Unidade Orçamentária:</strong> {{ registro_selecionado.unidade.__str__ }}
                  </div>
                  <div class="col-12" v-if="registro_selecionado.parlamentares && registro_selecionado.parlamentares.length">
                    <i class="fas fa-users mr-1"></i>
                    <strong>Parlamentares:</strong> {{ registro_selecionado.parlamentares.map(p => p.__str__).join(', ') }}
                  </div>
                </div>
              </div>
            </div>

            <b-tabs class="c-tabs-detalhe" content-class="mt-0" small>
              <b-tab active>
                <template #title>
                  Prestação de Contas
                  <b-badge variant="secondary" pill class="ml-1" v-if="prestacaocontaregistro">{{ prestacaocontaregistro.length }}</b-badge>
                </template>
                <div v-if="prestacaocontaregistro === null" class="text-center py-3">
                  <b-spinner small></b-spinner> Carregando...
                </div>
                <div v-else-if="prestacaocontaregistro.length === 0" class="text-muted text-center py-3">
                  Nenhum registro de prestação de contas encontrado.
                </div>
                <b-table v-else
                  :items="prestacaocontaregistro"
                  :fields="prestacao_fields"
                  :sort-by.sync="sortBy"
                  :sort-desc.sync="sortDesc"
                  small striped hover
                  class="mb-0 text-center c-prestacao-table"
                >
                  <template #cell(prestacao_conta)="data">
                    <a v-if="data.value && data.item.link_detail_backend" :href="data.item.link_detail_backend" target="_blank" class="small" :title="data.value.__str__">{{ data.value.data_envio ? data.value.data_envio.split('-').reverse().join('/') : '—' }}</a>
                    <span v-else class="small">{{ data.value && data.value.data_envio ? data.value.data_envio.split('-').reverse().join('/') : '—' }}</span>
                  </template>
                  <template #cell(detalhamento)="data">
                    <span class="small">{{ data.value || '—' }}</span>
                  </template>
                  <template #cell(situacao)="data">
                    <b-badge :variant="situacao_variant(data.value)">{{ situacao_label(data.value) }}</b-badge>
                  </template>
                </b-table>
              </b-tab>

              <b-tab v-if="registro_selecionado.__label__ === 'loa_emendaloa'">
                <template #title>
                  Ajustes vinculados à Emenda
                  <b-badge variant="secondary" pill class="ml-1" v-if="ajustes_emendas_selecionados">{{ ajustes_emendas_selecionados.length }}</b-badge>
                </template>
                <div v-if="ajustes_emendas_selecionados === null" class="text-center py-2">
                  <b-spinner small></b-spinner> Carregando...
                </div>
                <div v-else-if="ajustes_emendas_selecionados.length === 0" class="text-muted small py-3 text-center">
                  Nenhum ajuste vinculado a esta emenda.
                </div>
                <b-table v-else
                  :items="ajustes_emendas_selecionados"
                  :fields="ajustes_fields"
                  small striped hover
                  class="mb-0"
                >
                  <template #cell(str_valor)="data">
                    <span class="text-nowrap">R$ {{ data.value }}</span>
                  </template>
                  <template #cell(descricao)="data">
                    <a :href="data.item.link_detail_backend" target="_blank" class="small">{{ data.value }}</a>
                  </template>
                  <template #cell(oficio_ajuste_loa)="data">
                    <a v-if="data.value && data.value.link_detail_backend"
                      :href="data.value.link_detail_backend"
                      target="_blank"
                      class="btn btn-sm btn-outline-secondary"
                      title="Abrir ofício"
                    >
                      <i class="fas fa-external-link-alt mr-1"></i>{{ data.value.__str__ || 'Ofício' }}
                    </a>
                    <span v-else class="small">{{ data.value ? data.value.__str__ : '—' }}</span>
                  </template>
                </b-table>
              </b-tab>
            </b-tabs>
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
      ajustes_emendas_selecionados: [],
      prestacaocontaregistro: null,
      sortBy: 'prestacao_conta',
      sortDesc: false,
      fetching: false
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
        { key: 'prestacao_conta', label: 'Prestação de Conta', sortable: true },
        { key: 'detalhamento', label: 'Detalhamento' },
        { key: 'situacao', label: 'Situação' }
      ]
    },
    ajustes_fields: function () {
      return [
        { key: 'str_valor', label: 'Valor' },
        { key: 'descricao', label: 'Descrição' },
        { key: 'oficio_ajuste_loa', label: 'Ofício' }
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
            const val = this.filters_value[f]
            query[f] = (typeof val === 'object' && val !== null && !Array.isArray(val)) ? val.id : val
          }
        })
        this.$router.replace({ query })
        this.fetch()
      }
    }
  },
  methods: {
    resetFilters () {
      this.filters_value.unidade = null
      this.filters_value.parlamentares = null
      this.filters_value.situacao = []
      this.filters_value.emendas = 'True'
      this.filters_value.ajustes = 'True'
      this.filters_value.search = ''
    },
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
      this.prestacaocontaregistro = null
      this.ajustes_emendas_selecionados = null

      const params = {
        [registro.__label__ === 'loa_emendaloa' ? 'emendaloa' : 'registro_ajuste']: registro.id,
        get_all: 'True',
        expand: 'prestacao_conta'
      }
      this.utils.fetch({
        app: 'loa',
        model: 'prestacaocontaregistro',
        params
      })
        .then((response) => {
          this.prestacaocontaregistro = response.data
        })

      if (registro.__label__ === 'loa_emendaloa') {
        this.fetch_registroajusteloa(registro)
      }
    },
    fetch_registroajusteloa (registro) {
      const params = {
        emendaloa: registro.id,
        get_all: 'True',
        expand: 'oficio_ajuste_loa'
      }
      this.utils.fetch({
        app: 'loa',
        model: 'registroajusteloa',
        params
      })
        .then((response) => {
          this.ajustes_emendas_selecionados = response.data
        })
    },

    fetch () {
      this.registro_selecionado = null
      this.prestacaocontaregistro = null
      this.ajustes_emendas_selecionados = null
      this.fetching = true

      const promises = {}
      const fetchEmendas = (this.filters_value.emendas === 'True') | (this.filters_value.ajustes === 'False' && this.filters_value.emendas === 'False')
      const fetchAjustes = (this.filters_value.ajustes === 'True') | (this.filters_value.ajustes === 'False' && this.filters_value.emendas === 'False')

      if (fetchEmendas) {
        const params_emendas = {
          loa: this.loa.id,
          'o': 'fase,materia__tipo__sigla,materia__numero',
          exclude: 'search;parlamentares.metadata',
          include: 'parlamentares.id,__str__;unidade.id,__str__',
          expand: 'parlamentares;unidade',
          get_all: 'True', // parâmetro para retornar todas as emendas sem paginação, visto que o número de emendas é relativamente baixo
          situacao: this.filters_value.situacao.join(',')
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
        promises['emendas'] = this.utils.fetch({
          app: 'loa',
          model: 'emendaloa',
          params: params_emendas
        })
      }

      if (fetchAjustes) {
        const params_ajustes = {
          oficio_ajuste_loa__loa: this.loa.id,
          exclude: 'search',
          'o': 'parlamentares_valor__nome_parlamentar'
        }
        if (this.filters_value.unidade && typeof this.filters_value.unidade === 'object') {
          params_ajustes['unidade'] = this.filters_value.unidade.id
        }
        if (this.filters_value.search) {
          params_ajustes['search'] = this.filters_value.search
        }
        if (this.filters_value.parlamentares && typeof this.filters_value.parlamentares === 'object') {
          params_ajustes['parlamentares_valor'] = this.filters_value.parlamentares.id
        }
        params_ajustes['situacao'] = this.filters_value.situacao.join(',')
        params_ajustes['get_all'] = 'True' // parâmetro para retornar todos os ajustes sem paginação, visto que o número de ajustes é relativamente baixo

        promises['ajustes'] = this.utils.fetch({
          app: 'loa',
          model: 'registroajusteloa',
          params: params_ajustes
        })
      }

      const keys = Object.keys(promises)
      return Promise.all(Object.values(promises)).then((responses) => {
        const newResults = { 'emendas': {}, 'ajustes': {} }
        keys.forEach((key, i) => {
          newResults[key] = responses[i].data
        })
        this.results = newResults
      }).finally(() => {
        this.fetching = false
      })
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
                } else if (f === 'parlamentares') {
                  // parlamentares é salvo como id na QS, precisamos encontrar o objeto correspondente
                  const pid = parseInt(query[f])
                  if (pid && t.loa.parlamentares) {
                    const found = t.loa.parlamentares.find(p => p.id === pid)
                    if (found) {
                      t.filters_value[f] = found
                    }
                  }
                } else if (f === 'unidade') {
                  // unidade é salvo como id na QS, precisamos encontrar o objeto no ModelSelect
                  const uid = parseInt(query[f])
                  if (uid) {
                    t.$nextTick(() => {
                      const unidadeSelect = t.$refs.unidadeSelect
                      if (unidadeSelect) {
                        const checkOptions = () => {
                          const opt = unidadeSelect.options.find(o => o.value && o.value.id === uid)
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

<style scoped>
.c-fields {
  border-radius: 0.375rem;
}
.c-fields-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #555;
  margin-bottom: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.c-fields .row > div >>> select,
.c-fields .row > div >>> input,
.c-fields .row > div >>> .form-control {
  height: calc(1.5em + 0.5rem + 2px);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
.c-fields-check-group {
  background-color: #fff;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.875rem;
}
.c-fields-check-group >>> .custom-control-label {
  font-size: 0.8rem;
  line-height: 1.6;
}

.c-emendas-ajustes-header {
  background-color: #f8f9fa;
  border: 1px solid rgba(0, 0, 0, 0.125);
  border-bottom: none;
  border-radius: 0.25rem 0.25rem 0 0;
  padding: 0.4rem 0.75rem;
  margin-bottom: 0;
  font-weight: 600;
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.c-emendas-ajustes .list-group .list-group-item:first-child {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}
.c-emendas-ajustes .list-group-item.active {
  z-index: 0;
}
@media (max-width: 767.98px) {
  .c-emendas-ajustes {
    max-height: 50vh;
    overflow-y: auto;
    margin-bottom: 1em;
  }
}
.c-tabs-detalhe >>> .nav-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}
.c-tabs-detalhe >>> .nav-tabs .nav-link {
  font-size: 0.85rem;
  font-weight: 600;
  color: #555;
  padding: 0.4rem 0.75rem;
}
.c-tabs-detalhe >>> .nav-tabs .nav-link.active {
  color: #212529;
  border-color: rgba(0, 0, 0, 0.125) rgba(0, 0, 0, 0.125) #fff;
}
.c-tabs-detalhe >>> .tab-content {
  border: 1px solid rgba(0, 0, 0, 0.125);
  border-top: none;
  border-radius: 0 0 0.25rem 0.25rem;
}
.c-prestacao-table >>> thead th[aria-sort] {
  cursor: pointer;
  position: relative;
  padding-right: 1.5em;
}
.c-prestacao-table >>> thead th[aria-sort]::after {
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  font-size: 0.7em;
  position: absolute;
  right: 0.5em;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.4;
  content: '\f0dc';
}
.c-prestacao-table >>> thead th[aria-sort="ascending"]::after {
  content: '\f0de';
  opacity: 1;
}
.c-prestacao-table >>> thead th[aria-sort="descending"]::after {
  content: '\f0dd';
  opacity: 1;
}
</style>
