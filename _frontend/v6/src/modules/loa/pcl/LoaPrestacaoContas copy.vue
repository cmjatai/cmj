<template>
  <div
    ref="pclEl"
    class="loa-pcl container"
  >
    <div class="header-area">
      <div class="inner-header d-flex flex-column gap-2">
        <div class="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between gap-2">
          <div class="d-flex gap-2 flex-column">
            <h3 class="pcl-title mb-0">
              <FontAwesomeIcon
                icon="landmark"
                class="me-2 title-icon"
              />
              Emendas Impositivas - Jataí - GO
            </h3>
          </div>
          <button
            class="btn-fullscreen"
            :title="isFullscreen ? 'Sair do fullscreen' : 'Fullscreen'"
            @click="toggleFullscreen"
          >
            <FontAwesomeIcon :icon="isFullscreen ? 'compress' : 'expand'" />
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="loa.id"
      class="container-fluid mt-2 mb-2"
    >
      <PclFiltros
        v-model="filtersValue"
        :disabled="!ready || !firstPageLoaded"
        :parlamentares-choice="parlamentaresChoice"
        :loa-id="loa.id"
        :loas-choice="loasChoice"
        :loa-value="loa"
        :total-items="emendasAjustesList.length"
        :page-size="pageSize"
        :current-page="currentPage"
        :fetching="fetching"
        @update:page-size="onPageSizeChange"
        @update:current-page="onPageChange"
        @reset="resetFilters"
        @loa-change="onLoaChange"
      />

      <PclTotalizacao
        v-if="!fetching && emendasAjustesList.length"
        :lista="emendasAjustesList"
        :parlamentar-selecionado="filtersValue.parlamentares ? parlamentarObjById(filtersValue.parlamentares) : null"
        class="mt-3"
      />

      <div
        class="pcldetalhe-list"
        v-if="emendasAjustesList.length || fetching"
      >
        <template
          v-for="item in paginatedList"
          :key="item.__label__ + '_' + item.id"
        >
          <PclDetalheEmenda
            v-if="item.__label__ === 'loa_emendaloa'"
            :registro="item"
            @filter-unidade="applyUnidadeFilter"
            @filter-entidade="applyEntidadeFilter"
            @filter-parlamentar="applyParlamentarFilter"
          />
          <PclDetalheAjuste
            v-else
            :registro="item"
            @search-emenda="val => filtersValue = { ...filtersValue, search: val, ajustes: 'False', emendas_tipos: [] }"
            @filter-unidade="applyUnidadeFilter"
            @filter-parlamentar="applyParlamentarFilter"
          />
        </template>
      </div>
      <div
        v-else-if="ready"
        class="card text-muted text-center my-3 p-3 mx-5 fw-bold"
      >
        Nenhum resultado encontrado para os filtros selecionados.
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref, watch, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSyncStore } from '~@/stores/SyncStore'
import PclFiltros from './PclFiltros.vue'
import PclTotalizacao from './PclTotalizacao.vue'
import PclDetalheEmenda from './PclDetalheEmenda.vue'
import PclDetalheAjuste from './PclDetalheAjuste.vue'

const EventBus = inject('EventBus')
const syncStore = useSyncStore()
const route = useRoute()
const router = useRouter()

const pclEl = ref(null)
const isFullscreen = ref(false)
const ready = ref(false)
const fetching = ref(false)
const firstPageLoaded = ref(false)
const currentPage = ref(1)
const pageSize = ref(Number(localStorage.getItem('portalcmj_page_size')) || 10)

const FILTER_KEYS = ['unidade', 'entidade', 'parlamentares', 'situacao', 'emendas_tipos', 'ajustes', 'search']

const filtersValue = ref({
  loa: null,
  unidade: null,
  entidade: null,
  parlamentares: null,
  situacao: [],
  emendas_tipos: [],
  ajustes: 'False',
  search: ''
})

const results = ref({ emendas: [], ajustes: [] })
let _fetchId = 0

// --- Fullscreen ---
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    pclEl.value?.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}
const onFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const parlamentaresChoice = computed(() => {
  if (!filtersValue.value.loa?.parlamentares?.length) return []
  const parlCache = syncStore.data_cache?.parlamentares_parlamentar || {}
  const items = filtersValue.value.loa.parlamentares.map(pId => {
    const p = parlCache[pId] || { id: pId, nome_parlamentar: `#${pId}` }
    return { value: p.id, text: p.nome_parlamentar || p.__str__ || `#${p.id}` }
  })
  if (items.length > 1) {
    return [{ value: null, text: '----------------' }, ...items]
  }
  return items
})

function parlamentarObjById (pId) {
  if (!pId) return null
  if (typeof pId === 'object') return pId
  return syncStore.data_cache?.parlamentares_parlamentar?.[pId] || { id: pId }
}

const emendasAjustesList = computed(() => {
  const emendas = Array.isArray(results.value.emendas) ? results.value.emendas : []
  const ajustes = Array.isArray(results.value.ajustes) ? results.value.ajustes : []
  return [...emendas, ...ajustes]
})

const paginatedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return emendasAjustesList.value.slice(start, start + pageSize.value)
})

// --- Filter methods ---
function applyUnidadeFilter (unidade) {
  const uid = unidade?.id
  if (!uid) return
  filtersValue.value = { ...filtersValue.value, unidade: uid }
}

function applyParlamentarFilter (parlamentar) {
  const pid = parlamentar?.id
  if (!pid) return
  filtersValue.value = { ...filtersValue.value, parlamentares: pid }
}

function applyEntidadeFilter (entidade) {
  const eid = entidade?.id
  if (!eid) return
  filtersValue.value = {
    ...filtersValue.value,
    entidade: eid,
    emendas_tipos: ['10', '99'],
    ajustes: 'False'
  }
}

function resetFilters () {
  currentPage.value = 1
  filtersValue.value = {
    unidade: null,
    entidade: null,
    parlamentares: null,
    situacao: [],
    emendas_tipos: [],
    ajustes: 'False',
    search: ''
  }
}

function onPageSizeChange (size) {
  pageSize.value = size
  currentPage.value = 1
  localStorage.setItem('portalcmj_page_size', size)
}

function onPageChange (page) {
  const totalPages = Math.max(1, Math.ceil(emendasAjustesList.value.length / pageSize.value))
  currentPage.value = Math.max(1, Math.min(page, totalPages))
}

function onLoaChange (loaId) {
  if (!loaId || loaId === filtersValue.value.loa?.id) return
  const query = {}
  FILTER_KEYS.forEach(f => {
    if (f === 'unidade') return
    const val = filtersValue.value[f]
    if (val === null || val === undefined) return
    if (Array.isArray(val)) query[f] = val.join(',')
    else query[f] = val
  })
  // Reload with new LOA
  filtersValue.value = { ...filtersValue.value, loa: { id: loaId }, unidade: null }
  ready.value = false
  initLoa(loaId)
}

// --- Sync query params ---
function syncQueryParams () {
  const query = {}
  FILTER_KEYS.forEach(f => {
    const val = filtersValue.value[f]
    if (val !== null && val !== undefined) {
      if (Array.isArray(val)) {
        if (val.length) query[f] = val.join(',')
      } else {
        query[f] = val
      }
    }
  })
  router.replace({ query }).catch(err => {
    if (err.name !== 'NavigationDuplicated') throw err
  })
}

function applyQueryFilters () {
  const query = route.query
  FILTER_KEYS.forEach(f => {
    if (query[f] === undefined) return
    if (f === 'situacao' || f === 'emendas_tipos') {
      filtersValue.value[f] = typeof query[f] === 'string' ? query[f].split(',') : query[f]
    } else if (f === 'parlamentares') {
      const pid = parseInt(query[f])
      if (pid) filtersValue.value[f] = pid
    } else if (f === 'unidade') {
      const uid = parseInt(query[f])
      if (uid) filtersValue.value[f] = uid
    } else if (f === 'entidade') {
      const eid = parseInt(query[f])
      if (eid) filtersValue.value[f] = eid
    } else {
      filtersValue.value[f] = query[f]
    }
  })
}

// --- Fetch logic using syncStore ---
async function fetchData () {
  if (!loa.value.id) return

  _fetchId++
  const currentFetchId = _fetchId
  fetching.value = true
  firstPageLoaded.value = false
  results.value = { emendas: [], ajustes: [] }

  const emendasTipos = _.filter(filtersValue.value.emendas_tipos, v => v)
  const shouldFetchEmendas =
    (Array.isArray(emendasTipos) && emendasTipos.length > 0) ||
    (filtersValue.value.ajustes === 'False' && (!Array.isArray(emendasTipos) || emendasTipos.length === 0))
  const shouldFetchAjustes =
    (filtersValue.value.ajustes === 'True') ||
    (filtersValue.value.ajustes === 'False' && (!Array.isArray(emendasTipos) || emendasTipos.length === 0))

  const pending = []

  if (shouldFetchEmendas) {
    const params = {
      loa: loa.value.id,
      o: 'materia__tipo__sigla,materia__numero',
      exclude: 'search;metadata',
      include: 'parlamentares.id,__str__,fotografia;unidade.id,__str__;materia.id',
      expand: 'parlamentares;unidade;materia;entidade',
      situacao: filtersValue.value.situacao.join(',')
    }
    if (filtersValue.value.unidade) params.unidade = filtersValue.value.unidade
    if (filtersValue.value.entidade) params.entidade = filtersValue.value.entidade
    if (filtersValue.value.parlamentares) params.parlamentares = filtersValue.value.parlamentares
    if (filtersValue.value.search) params.search = filtersValue.value.search
    if (Array.isArray(emendasTipos) && emendasTipos.length > 0) params.tipo__in = emendasTipos.join(',')

    pending.push(
      syncStore.fetchSync({
        app: 'loa',
        model: 'emendaloa',
        params: { ...params, page_size: 20 }
      }).then(cache => {
        if (_fetchId !== currentFetchId) return
        const items = cache ? Object.values(cache) : []
        // Filter to match current loa and params
        const filtered = items.filter(e => {
          if (e.loa !== loa.value.id) return false
          if (filtersValue.value.unidade && e.unidade !== filtersValue.value.unidade) return false
          if (filtersValue.value.entidade && e.entidade !== filtersValue.value.entidade) return false
          if (filtersValue.value.parlamentares) {
            if (!e.parlamentares?.includes(filtersValue.value.parlamentares)) return false
          }
          if (Array.isArray(emendasTipos) && emendasTipos.length > 0) {
            if (!emendasTipos.includes(String(e.tipo))) return false
          }
          return true
        })
        results.value = { ...results.value, emendas: filtered }
        firstPageLoaded.value = true
      })
    )
  }

  if (shouldFetchAjustes) {
    const params = {
      oficio_ajuste_loa__loa: loa.value.id,
      exclude: 'search',
      include: 'parlamentares_valor.id,__str__,fotografia;oficio_ajuste_loa.id,__str__',
      expand: 'emendaloa.id,__str__;unidade;parlamentares_valor;oficio_ajuste_loa',
      o: 'parlamentares_valor__nome_parlamentar',
      page_size: 20
    }
    if (filtersValue.value.unidade) params.unidade = filtersValue.value.unidade
    if (filtersValue.value.entidade) params.entidade = filtersValue.value.entidade
    if (filtersValue.value.search) params.search = filtersValue.value.search
    if (filtersValue.value.parlamentares) params.parlamentares_valor = filtersValue.value.parlamentares
    params.situacao = filtersValue.value.situacao.join(',')

    pending.push(
      syncStore.fetchSync({
        app: 'loa',
        model: 'registroajusteloa',
        params
      }).then(cache => {
        if (_fetchId !== currentFetchId) return
        const items = cache ? Object.values(cache) : []
        const filtered = items.filter(a => {
          const oficioLoa = a.oficio_ajuste_loa
          if (typeof oficioLoa === 'object') {
            if (oficioLoa?.loa !== loa.value.id) return false
          }
          if (filtersValue.value.unidade && a.unidade !== filtersValue.value.unidade) return false
          return true
        })
        results.value = { ...results.value, ajustes: filtered }
        firstPageLoaded.value = true
      })
    )
  }

  if (!pending.length) {
    fetching.value = false
    firstPageLoaded.value = true
    return
  }

  await Promise.all(pending).finally(() => {
    if (_fetchId === currentFetchId) {
      fetching.value = false
      firstPageLoaded.value = true
    }
  })
}

// --- Watch filters ---
watch(filtersValue, () => {
  if (!ready.value) return
  currentPage.value = 1
  syncQueryParams()
  fetchData()
}, { deep: true })

// --- Init ---
async function initLoa (loaId) {
  const loaCache = await syncStore.fetchSync({
    app: 'loa',
    model: 'loa',
    id: loaId,
    params: {
      expand: 'parlamentares',
      include: 'parlamentares.id,nome_parlamentar'
    }
  })

  if (loaCache && loaCache[loaId]) {
    loa.value = loaCache[loaId]
  } else if (loaCache) {
    loa.value = Object.values(loaCache)[0] || { id: loaId }
  }

  const loasCache = await syncStore.fetchSync({
    app: 'loa',
    model: 'loa',
    params: {
      ano__gte: 2023,
      get_all: 'True',
      o: '-ano'
    }
  })

  if (loasCache) {
    loasList.value = _.orderBy(Object.values(loasCache).filter(l => l.ano >= 2023), ['ano'], ['desc'])
  }

  applyQueryFilters()
  ready.value = true
  fetchData()
}

async function resolveInitialLoaId () {
  // Tenta pegar o ID da LOA da query string ou do cache
  if (route.query.loa) {
    return parseInt(route.query.loa)
  }
  // Busca a LOA mais recente disponível
  const loasCache = await syncStore.fetchSync({
    app: 'loa',
    model: 'loa',
    params: { ano__gte: 2023, get_all: 'True', o: '-ano' }
  })
  if (loasCache) {
    const loas = _.orderBy(Object.values(loasCache), ['ano'], ['desc'])
    if (loas.length) return loas[0].id
  }
  return null
}

onMounted(async () => {
  EventBus.emit('side:close-sideleft')
  EventBus.emit('side:close-sideright')
  document.addEventListener('fullscreenchange', onFullscreenChange)

  const loaId = await resolveInitialLoaId()
  if (loaId) {
    loa.value = { id: loaId }
    initLoa(loaId)
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})

watch(() => loa.value, (val) => {
  if (val?.ano) {
    document.title = `LOA ${val.ano} - Emendas Impositivas - Jataí`
  } else {
    document.title = 'LOA - Emendas Impositivas - Jataí'
  }
}, { deep: true })
</script>

<style lang="scss" scoped>
.loa-pcl {
  &:fullscreen {
    background: var(--bs-body-bg);
    overflow: auto;
  }
  background: linear-gradient(135deg, #f1f3f5 30%, #e9ecef 50%, #f1f3f5 100%);

  [data-bs-theme="dark"] & {
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
  }
}

.btn-fullscreen {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--bs-border-color);
  background: var(--bs-tertiary-bg);
  color: var(--bs-body-color);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;

  &:hover {
    background: var(--bs-secondary-bg);
    color: var(--bs-primary);
    border-color: var(--bs-primary);
  }
}

.header-area {
  .inner-header {
    padding: 0.5rem;
  }
}

.pcl-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--bs-body-color);
  white-space: nowrap;

  .title-icon {
    color: var(--bs-primary);
  }
}

.pcldetalhe-list {
  margin: 15px 0 30px;
}
</style>
