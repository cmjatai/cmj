<template>
  <div class="pcl-filtros">
    <div class="row">
      <i class="fas fa-filter text-secondary mr-2"></i>
      <h4><strong class="text-primary">Filtrar Dados</strong></h4>
    </div>
    <div class="row" >
      <div v-if="loasChoice.length" class="col-xl-1 col-md-2 col-4 mb-2 px-1">
        <label class="pcl-filtros-label">EXERCÍCIO</label>
        <b-form-select
          :value="selectedLoaId"
          :options="loasChoice"
          @change="val => $emit('loa-change', val)"
          :disabled="disabled"
        ></b-form-select>
      </div>
      <div class="col-lg col-md-10 col-8 mb-2 px-1">
        <label class="pcl-filtros-label">Pesquisa</label>
        <b-input-group>
          <b-form-input
            ref="searchInput"
            type="search"
            :value="value.search"
            @change="val => updateFilter('search', val)"
            placeholder="Filtre por termos nos Ajustes e Emendas"
            :disabled="filtersDisabled"
          ></b-form-input>
          <b-input-group-append>
            <b-button class="btn-secondary" @click="$refs.searchInput.$el.blur()" title="Pesquisar">
              <i class="fas fa-search"></i>
            </b-button>
          </b-input-group-append>
        </b-input-group>
      </div>
      <div class="col-lg-2 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Parlamentares</label>
        <b-form-select
          @change="val => updateFilter('parlamentares', val)"
          :value="value.parlamentares"
          :options="parlamentaresChoice"
          :disabled="filtersDisabled"
        ></b-form-select>
      </div>
      <div class="col-lg-3 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Entidades</label>
        <model-select
          @change="val => updateFilter('entidade', val)"
          :value="value.entidade"
          app="loa"
          model="entidade"
          choice="__str__"
          ordering="nome_fantasia"
          ref="entidadeSelect"
          :required="false"
          :extra_query="`${qsEmendaLoa}&ativo=True`"
          :disabled="filtersDisabled"
        ></model-select>
      </div>
      <div class="col-lg-3 col-md-4 mb-2 px-1">
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
          :disabled="filtersDisabled"
        ></model-select>
      </div>
    </div>
    <div class="row align-items-end mt-2">
      <div class="col-lg-auto col-12 mb-2 px-1">
        <label class="pcl-filtros-label">Documentos</label>
        <div class="pcl-filtros-check-group d-flex flex-wrap">
          <b-form-checkbox-group
            :checked="value.emendas_tipos"
            @change="val => updateFilter('emendas_tipos', val)"
            :disabled="filtersDisabled"
          >
            <b-form-checkbox class="mr-3" value="10">Impositivas da Saúde</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="99">Imp. de Áreas Diversas</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="0">Modificativas</b-form-checkbox>
          </b-form-checkbox-group>
          <b-form-checkbox
            :checked="value.ajustes"
            @change="val => updateFilter('ajustes', val)"
            value="True"
            unchecked-value="False"
            :disabled="filtersDisabled"
          >Registros de Ajustes</b-form-checkbox>
        </div>
      </div>
      <div class="col-lg-auto col mb-2 px-1">
        <label class="pcl-filtros-label">Situação</label>
        <div class="pcl-filtros-check-group d-flex flex-wrap">
          <b-form-checkbox-group :checked="value.situacao" @change="val => updateFilter('situacao', val)" :disabled="filtersDisabled">
            <b-form-checkbox class="mr-3" value="EM_EXECUCAO">Em Execução</b-form-checkbox>
            <b-form-checkbox class="mr-3" value="FINALIZADO">Finalizado</b-form-checkbox>
            <b-form-checkbox value="IMPEDIMENTO">Impedidas em definitivo</b-form-checkbox>
          </b-form-checkbox-group>
        </div>
      </div>
      <div class="col-auto ml-auto mb-1 px-1">
        <button class="btn btn-sm btn-secondary" @click="$emit('reset')" title="Limpar todos os filtros">
          <i class="fas fa-times mr-1"></i>Limpar
        </button>
      </div>
    </div>
    <div v-if="totalItems > 0" class="pcl-pagination d-flex align-items-center mt-2 pt-2 border-top">
      <div class="d-flex align-items-center mr-3 px-1">
        <small class="text-muted text-uppercase font-weight-bold mr-2" style="font-size:.7rem;letter-spacing:.03em;">Exibir</small>
        <b-form-select
          :value="pageSize"
          :options="pageSizeOptions"
          @change="val => $emit('update:page-size', Number(val))"
          size="sm"
          class="pcl-page-size-select"
        ></b-form-select>
      </div>
      <small class="text-muted mr-auto" style="font-size:.8rem;">{{ paginationLabel }}
        <b-spinner v-if="fetching" small variant="secondary" class="ml-2" style="vertical-align:middle;"></b-spinner>
      </small>
      <nav class="d-flex align-items-center">
        <button
          class="pcl-page-btn"
          :disabled="currentPage <= 1"
          @click="$emit('update:current-page', 1)"
          title="Primeira página"
        ><i class="fas fa-angle-double-left"></i></button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage <= 1"
          @click="$emit('update:current-page', currentPage - 1)"
          title="Página anterior"
        ><i class="fas fa-chevron-left"></i></button>
        <button
          v-for="p in visiblePages"
          :key="p"
          class="pcl-page-btn"
          :class="{ active: p === currentPage }"
          @click="$emit('update:current-page', p)"
        >{{ p }}</button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage >= totalPages"
          @click="$emit('update:current-page', currentPage + 1)"
          title="Próxima página"
        ><i class="fas fa-chevron-right"></i></button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage >= totalPages"
          @click="$emit('update:current-page', totalPages)"
          title="Última página"
        ><i class="fas fa-angle-double-right"></i></button>
      </nav>
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
    },
    qsEmendaLoa: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loasChoice: {
      type: Array,
      default: () => []
    },
    loaValue: {
      type: Object,
      default: null
    },
    totalItems: {
      type: Number,
      default: 0
    },
    pageSize: {
      type: Number,
      default: 25
    },
    currentPage: {
      type: Number,
      default: 1
    },
    fetching: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    selectedLoaId () {
      return this.loaValue && this.loaValue.id ? this.loaValue.id : null
    },
    filtersDisabled () {
      return this.disabled
    },
    pageSizeOptions () {
      return [
        { value: 10, text: '10' },
        { value: 25, text: '25' },
        { value: 50, text: '50' },
        { value: 100, text: '100' }
      ]
    },
    totalPages () {
      return Math.max(1, Math.ceil(this.totalItems / this.pageSize))
    },
    paginationLabel () {
      const start = (this.currentPage - 1) * this.pageSize + 1
      const end = Math.min(this.currentPage * this.pageSize, this.totalItems)
      const suffix = this.fetching ? ' (carregando...)' : ''
      return `${start}–${end} de ${this.totalItems}${suffix}`
    },
    visiblePages () {
      const pages = []
      const total = this.totalPages
      const current = this.currentPage
      let start = Math.max(1, current - 2)
      let end = Math.min(total, current + 2)
      if (end - start < 4) {
        if (start === 1) end = Math.min(total, start + 4)
        else start = Math.max(1, end - 4)
      }
      for (let i = start; i <= end; i++) pages.push(i)
      return pages
    }
  },
  methods: {
    updateFilter (key, val) {
      const patch = { ...this.value, [key]: val }
      if (key === 'entidade' && val) {
        patch.emendas_tipos = ['10', '99']
        patch.ajustes = 'False'
      }
      this.$emit('input', patch)
    },
    /**
     * Permite ao componente pai acessar o ref unidadeSelect
     * para restauração de filtros via query string.
     */
    getUnidadeSelectRef () {
      return this.$refs.unidadeSelect
    },
    getEntidadeSelectRef () {
      return this.$refs.entidadeSelect
    }
  }
}
</script>

<style lang="scss" scoped>
.pcl-filtros {
  border-radius: 0 0 0.25rem 0.25rem;
  background-color: white;
  margin: -16px -15px 0;
  padding: 1rem 1.5rem 0.5rem;
  border-bottom: 1px solid #dee2e6;
  // box-shadow: 0rem 0.2rem 0.5rem rgba(0, 0, 0, 0.05);
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

/* Pagination */
.pcl-pagination {
  gap: 0.25rem;
}
.pcl-page-size-select {
  width: 4.5rem !important;
  height: calc(1.5em + 0.5rem + 2px);
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
.pcl-page-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.85rem;
  height: 1.85rem;
  padding: 0 0.35rem;
  margin: 0 1px;
  font-size: 0.78rem;
  font-weight: 500;
  color: #555;
  background: #fff;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pcl-page-btn:hover:not(:disabled):not(.active) {
  background: #e9ecef;
  border-color: #adb5bd;
  color: #333;
}
.pcl-page-btn.active {
  background: #6c757d;
  border-color: #6c757d;
  color: #fff;
  font-weight: 600;
}
.pcl-page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ===== Responsivo < 992px ===== */
@media (max-width: 991.98px) {
  .pcl-filtros {
  }
  .pcl-pagination {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
}

/* ===== Responsivo < 768px ===== */
@media (max-width: 767.98px) {
  .pcl-filtros-label {
    font-size: 0.7rem;
  }
  .pcl-filtros-check-group {
    font-size: 0.8rem;
    padding: 0.15rem 0.35rem;
  }
  .pcl-filtros-check-group >>> .custom-control-label {
    font-size: 0.72rem;
  }
  .pcl-pagination {
    flex-direction: column;
    align-items: stretch !important;
    gap: 0.5rem;
  }
  .pcl-pagination nav {
    justify-content: center;
  }
  .pcl-pagination > small {
    text-align: center;
  }
}

/* ===== Responsivo < 425px ===== */
@media (max-width: 425px) {
  .pcl-filtros {
  }
  .pcl-filtros-check-group {
    font-size: 0.75rem;
    padding: 0.1rem 0.25rem;
  }
  .pcl-filtros-check-group >>> .custom-control-label {
    font-size: 0.68rem;
  }
  .pcl-page-btn {
    min-width: 1.6rem;
    height: 1.6rem;
    font-size: 0.7rem;
    padding: 0 0.2rem;
  }
  .pcl-page-size-select {
    width: 3.5rem !important;
    font-size: 0.7rem;
  }
}
</style>
