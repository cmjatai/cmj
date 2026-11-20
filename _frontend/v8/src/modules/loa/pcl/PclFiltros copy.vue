<template>
  <div class="pcl-filtros">
    <div class="row mb-1">
      <div class="col-auto d-flex align-items-center">
        <FontAwesomeIcon
          icon="filter"
          class="text-secondary me-2"
        />
        <h4 class="mb-0">
          <strong class="text-primary">Filtrar Dados</strong>
        </h4>
      </div>
    </div>
    <div class="row">
      <div
        class="col-xl-1 col-md-2 col-4 mb-2 px-1"
      >
        <label class="pcl-filtros-label">EXERCÍCIO</label>
        <b-form-select
          :model-value="selectedLoaId"
          :options="loasChoice"
          @update:model-value="val => emit('loa-change', val)"
          :disabled="disabled"
        />
      </div>
      <div class="col-lg col-md-10 col-8 mb-2 px-1">
        <label class="pcl-filtros-label">Pesquisa</label>
        <div class="input-group">
          <input
            ref="searchInput"
            type="search"
            class="form-control"
            :value="modelValue.search"
            @change="e => updateFilter('search', e.target.value)"
            placeholder="Filtre por termos nos Ajustes e Emendas"
            :disabled="filtersDisabled"
          >
          <button
            class="btn btn-secondary"
            @click="searchInput?.blur()"
            title="Pesquisar"
          >
            <FontAwesomeIcon icon="search" />
          </button>
        </div>
      </div>
      <div class="col-lg-2 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Parlamentares</label>
        <b-form-select
          :model-value="modelValue.parlamentares"
          :options="parlamentaresChoice"
          @update:model-value="val => updateFilter('parlamentares', val)"
          :disabled="filtersDisabled"
        />
      </div>
      <div class="col-lg-3 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Entidades</label>
        <b-form-select
          :model-value="modelValue.entidade"
          :options="entidadeOptions"
          @update:model-value="val => updateFilter('entidade', val)"
          :disabled="filtersDisabled"
        />
      </div>
      <div class="col-lg-3 col-md-4 mb-2 px-1">
        <label class="pcl-filtros-label">Unidade Orçamentária</label>
        <b-form-select
          :model-value="modelValue.unidade"
          :options="unidadeOptions"
          @update:model-value="val => updateFilter('unidade', val)"
          :disabled="filtersDisabled"
        />
      </div>
    </div>
    <div class="row align-items-end mt-2">
      <div class="col-lg-auto col-12 mb-2 px-1">
        <label class="pcl-filtros-label">Documentos</label>
        <div class="pcl-filtros-check-group d-flex flex-wrap">
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-tipo-10"
              value="10"
              :checked="modelValue.emendas_tipos.includes('10')"
              @change="toggleTipo('10')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-tipo-10"
            >Impositivas da Saúde</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-tipo-99"
              value="99"
              :checked="modelValue.emendas_tipos.includes('99')"
              @change="toggleTipo('99')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-tipo-99"
            >Imp. de Áreas Diversas</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-tipo-0"
              value="0"
              :checked="modelValue.emendas_tipos.includes('0')"
              @change="toggleTipo('0')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-tipo-0"
            >Modificativas</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-ajustes"
              :checked="modelValue.ajustes === 'True'"
              @change="updateFilter('ajustes', modelValue.ajustes === 'True' ? 'False' : 'True')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-ajustes"
            >Registros de Ajustes</label>
          </div>
        </div>
      </div>
      <div class="col-lg-auto col mb-2 px-1">
        <label class="pcl-filtros-label">Situação</label>
        <div class="pcl-filtros-check-group d-flex flex-wrap">
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-sit-exec"
              value="EM_EXECUCAO"
              :checked="modelValue.situacao.includes('EM_EXECUCAO')"
              @change="toggleSituacao('EM_EXECUCAO')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-sit-exec"
            >Em Execução</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-sit-fin"
              value="FINALIZADO"
              :checked="modelValue.situacao.includes('FINALIZADO')"
              @change="toggleSituacao('FINALIZADO')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-sit-fin"
            >Finalizado</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="checkbox"
              id="pcl-sit-imp"
              value="IMPEDIMENTO"
              :checked="modelValue.situacao.includes('IMPEDIMENTO')"
              @change="toggleSituacao('IMPEDIMENTO')"
              :disabled="filtersDisabled"
            >
            <label
              class="form-check-label"
              for="pcl-sit-imp"
            >Impedidas em definitivo</label>
          </div>
        </div>
      </div>
      <div class="col-auto ms-auto mb-1 px-1">
        <button
          class="btn btn-sm btn-secondary"
          @click="emit('reset')"
          title="Limpar todos os filtros"
        >
          <FontAwesomeIcon
            icon="times"
            class="me-1"
          />Limpar
        </button>
      </div>
    </div>
    <div
      v-if="totalItems > 0"
      class="pcl-pagination d-flex align-items-center justify-content-between mt-2 pt-2 border-top"
    >
      <div class="d-flex align-items-center">
        <div class="d-flex align-items-center me-3 px-1">
          <small
            class="text-muted text-uppercase fw-bold me-2"
            style="font-size:.7rem;letter-spacing:.03em;"
          >Exibir</small>
          <select
            class="form-select form-select-sm pcl-page-size-select"
            :value="pageSize"
            @change="e => emit('update:page-size', Number(e.target.value))"
          >
            <option
              v-for="opt in pageSizeOptions"
              :key="opt"
              :value="opt"
            >
              {{ opt }}
            </option>
          </select>
        </div>
        <small
          class="text-muted me-auto"
          style="font-size:.8rem;"
        >
          {{ paginationLabel }}
          <span
            v-if="fetching"
            class="spinner-border spinner-border-sm ms-2 text-secondary"
            role="status"
            style="vertical-align:middle;"
          />
        </small>
      </div>
      <nav class="d-flex align-items-center">
        <button
          class="pcl-page-btn"
          :disabled="currentPage <= 1"
          @click="emit('update:current-page', 1)"
          title="Primeira página"
        >
          <FontAwesomeIcon icon="angles-left" />
        </button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage <= 1"
          @click="emit('update:current-page', currentPage - 1)"
          title="Página anterior"
        >
          <FontAwesomeIcon icon="chevron-left" />
        </button>
        <button
          v-for="p in visiblePages"
          :key="p"
          class="pcl-page-btn"
          :class="{ active: p === currentPage }"
          @click="emit('update:current-page', p)"
        >
          {{ p }}
        </button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage >= totalPages"
          @click="emit('update:current-page', currentPage + 1)"
          title="Próxima página"
        >
          <FontAwesomeIcon icon="chevron-right" />
        </button>
        <button
          class="pcl-page-btn"
          :disabled="currentPage >= totalPages"
          @click="emit('update:current-page', totalPages)"
          title="Última página"
        >
          <FontAwesomeIcon icon="angles-right" />
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const props = defineProps({
  modelValue: { type: Object, required: true },
  parlamentaresChoice: { type: Array, default: () => [] },
  loaId: { type: [Number, String], default: null },
  disabled: { type: Boolean, default: false },
  loaValue: { type: Object, default: null },
  totalItems: { type: Number, default: 0 },
  pageSize: { type: Number, default: 25 },
  currentPage: { type: Number, default: 1 },
  fetching: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'update:page-size', 'update:current-page', 'reset', 'loa-change'])

const searchInput = ref(null)

const selectedLoaId = computed(() => props.loaValue?.id ?? null)
const filtersDisabled = computed(() => props.disabled)

const pageSizeOptions = [10, 25, 50, 100]

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.pageSize)))

const paginationLabel = computed(() => {
  const start = (props.currentPage - 1) * props.pageSize + 1
  const end = Math.min(props.currentPage * props.pageSize, props.totalItems)
  const suffix = props.fetching ? ' (carregando...)' : ''
  return `${start}–${end} de ${props.totalItems}${suffix}`
})

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = props.currentPage
  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(total, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const entidadeOptions = computed(() => {
  const cache = syncStore.data_cache?.loa_entidade
  if (!cache) return [{ value: null, text: '--- Selecione ---' }]
  const items = Object.values(cache)
    .filter(e => e.ativo !== false)
    .sort((a, b) => (a.nome_fantasia || '').localeCompare(b.nome_fantasia || ''))
  return [
    { value: null, text: '--- Selecione ---' },
    ...items.map(e => ({ value: e.id, text: e.__str__ || e.nome_fantasia }))
  ]
})

const unidadeOptions = computed(() => {
  const cache = syncStore.data_cache?.loa_unidadeorcamentaria
  if (!cache) return [{ value: null, text: '--- Selecione ---' }]
  const items = Object.values(cache)
    .filter(u => u.recebe_emenda_impositiva !== false)
    .sort((a, b) => (a.codigo || '').localeCompare(b.codigo || ''))
  return [
    { value: null, text: '--- Selecione ---' },
    ...items.map(u => ({ value: u.id, text: u.__str__ || `${u.codigo} - ${u.especificacao}` }))
  ]
})

function updateFilter (key, val) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

function toggleTipo (tipo) {
  const current = [...props.modelValue.emendas_tipos]
  const idx = current.indexOf(tipo)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(tipo)
  updateFilter('emendas_tipos', current)
}

function toggleSituacao (sit) {
  const current = [...props.modelValue.situacao]
  const idx = current.indexOf(sit)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(sit)
  updateFilter('situacao', current)
}

onMounted(() => {
  syncStore.fetchSync({
    app: 'loa',
    model: 'entidade',
    params: { loa: props.loaId, ativo: true, page_size: 100, get_all: true }
  })
  syncStore.fetchSync({
    app: 'loa',
    model: 'unidadeorcamentaria',
    params: { loa: props.loaId, recebe_emenda_impositiva: true, page_size: 100, get_all: true }
  })
})
</script>

<style lang="scss" scoped>
.pcl-filtros {
  border-radius: 0 0 0.25rem 0.25rem;
  background-color: var(--bs-body-bg);
  padding: 1rem 1.5rem 0.5rem;
  border-bottom: 1px solid var(--bs-border-color);
}

.pcl-filtros-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--bs-secondary-color);
  margin-bottom: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.pcl-filtros-check-group {
  background-color: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.25rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.875rem;

  .form-check-label {
    font-size: 0.8rem;
    line-height: 1.6;
  }
}

.pcl-pagination {
  gap: 0.25rem;
}

.pcl-page-size-select {
  width: 4.5rem !important;
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
  color: var(--bs-secondary-color);
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled):not(.active) {
    background: var(--bs-tertiary-bg);
    border-color: var(--bs-secondary-bg);
    color: var(--bs-body-color);
  }

  &.active {
    background: var(--bs-secondary);
    border-color: var(--bs-secondary);
    color: #fff;
    font-weight: 600;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

@media (max-width: 767.98px) {
  .pcl-filtros-label {
    font-size: 0.7rem;
  }
  .pcl-filtros-check-group {
    font-size: 0.8rem;
    padding: 0.15rem 0.35rem;

    .form-check-label {
      font-size: 0.72rem;
    }
  }
  .pcl-pagination {
    flex-direction: column;
    align-items: stretch !important;
    gap: 0.5rem;

    nav {
      justify-content: center;
    }
    > small {
      text-align: center;
    }
  }
}

@media (max-width: 425px) {
  .pcl-filtros-check-group {
    font-size: 0.75rem;
    padding: 0.1rem 0.25rem;

    .form-check-label {
      font-size: 0.68rem;
    }
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
