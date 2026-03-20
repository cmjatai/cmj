<template>
  <div class="pcl-filtros card card-body bg-light py-3 px-3 mb-0">
    <div class="row">
      <div class="col-md-5 mb-2">
        <label class="pcl-filtros-label">Pesquisa</label>
        <b-input-group size="sm">
          <b-form-input
            ref="searchInput"
            type="search"
            :value="value.search"
            @change="val => updateFilter('search', val)"
            placeholder="Filtre por termos nos Ajustes e Emendas"
          ></b-form-input>
          <b-input-group-append>
            <b-button class="btn-secondary" @click="$refs.searchInput.$el.blur()" title="Pesquisar">
              <i class="fas fa-search"></i>
            </b-button>
          </b-input-group-append>
        </b-input-group>
      </div>
      <div class="col-md-3 mb-2">
        <label class="pcl-filtros-label">Parlamentares</label>
        <b-form-select
          @change="val => updateFilter('parlamentares', val)"
          :value="value.parlamentares"
          :options="parlamentaresChoice"
          size="sm"
        ></b-form-select>
      </div>
      <div class="col-md-4 mb-2">
        <label class="pcl-filtros-label">Unidade Orçamentária</label>
        <model-select
          @change="val => updateFilter('unidade', val)"
          :value="value.unidade"
          app="loa"
          model="unidadeorcamentaria"
          choice="__str__"
          ordering="codigo"
          ref="unidadeSelect"
          :required="false"
          :extra_query="`${qsLoa}&recebe_emenda_impositiva=True`"
        ></model-select>
      </div>
      <div class="col-12 text-muted small mb-0">
        OBS: A não seleção de todos os filtros de cada categoria retorna todos os registros relacionados à LOA e, no caso de Emendas Modificativas, os filtros de situação são irrelevantes.
      </div>
    </div>
    <div class="row align-items-end mt-2">
      <div class="col-auto">
        <label class="pcl-filtros-label">Documentos</label>
        <div class="pcl-filtros-check-group d-flex flex-wrap">
          <b-form-checkbox-group
            :checked="value.emendas_tipos"
            @change="val => updateFilter('emendas_tipos', val)"
          >
            <b-form-checkbox class="mr-3" value="10">Impositivas da Saúde</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="99">Impositivas de Áreas Diversas</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="0">Modificativas</b-form-checkbox>
          </b-form-checkbox-group>
          <b-form-checkbox
            :checked="value.ajustes"
            @change="val => updateFilter('ajustes', val)"
            value="True"
            unchecked-value="False"
          >Registros de Ajustes</b-form-checkbox>
        </div>
      </div>
      <div class="col-auto">
        <label class="pcl-filtros-label">Situação</label>
        <div class="pcl-filtros-check-group d-flex">
          <b-form-checkbox-group :checked="value.situacao" @change="val => updateFilter('situacao', val)">
            <b-form-checkbox class="mr-3" value="EM_TRAMITACAO">Em Tramitação</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="FINALIZADO">Finalizado</b-form-checkbox>
            <b-form-checkbox value="IMPEDIMENTO">Imp. Técnico / Redefinição</b-form-checkbox>
          </b-form-checkbox-group>
        </div>
      </div>
      <div class="col-auto ml-auto">
        <button class="btn btn-sm btn-outline-secondary" @click="$emit('reset')" title="Limpar todos os filtros">
          <i class="fas fa-times mr-1"></i>Limpar
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'

export default {
  name: 'pcl-filtros',
  components: {
    ModelSelect
  },
  props: {
    value: {
      type: Object,
      required: true
    },
    parlamentaresChoice: {
      type: Array,
      default: () => []
    },
    qsLoa: {
      type: String,
      default: ''
    }
  },
  methods: {
    updateFilter (key, val) {
      this.$emit('input', { ...this.value, [key]: val })
    },
    /**
     * Permite ao componente pai acessar o ref unidadeSelect
     * para restauração de filtros via query string.
     */
    getUnidadeSelectRef () {
      return this.$refs.unidadeSelect
    }
  }
}
</script>

<style scoped>
.pcl-filtros {
  border-radius: 0.375rem;
}
.pcl-filtros-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #555;
  margin-bottom: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.pcl-filtros .row > div >>> select,
.pcl-filtros .row > div >>> input,
.pcl-filtros .row > div >>> .form-control {
  height: calc(1.5em + 0.5rem + 2px);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
.pcl-filtros-check-group {
  background-color: #fff;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.875rem;
}
.pcl-filtros-check-group >>> .custom-control-label {
  font-size: 0.8rem;
  line-height: 1.6;
}
</style>
