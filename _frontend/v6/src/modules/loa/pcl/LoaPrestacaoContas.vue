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
    <PclFiltros
      v-model="filtersValue"
    />
    <div class="container-fluid mt-2 mb-2">
      <div class="row">
        <div class="col-md-12">
          <div
            v-for="emenda in emendasList"
            :key="emenda.id"
          >
            <pre>{{ emenda }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, inject, ref, watch, computed } from 'vue'
import PclFiltros from './PclFiltros.vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const EventBus = inject('EventBus')
const pclEl = ref(null)
const isFullscreen = ref(false)

const filtersValue = ref({
  loa: null,
  unidade: null,
  entidade: null,
  parlamentar: null,
  situacao: [],
  emendas_tipos: [],
  ajustes: 'False',
  search: ''
})

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

const emendasList = computed(() => {
  const emendas = Object.values(syncStore.data_cache?.loa_emendaloa || {})
  return emendas.filter(e => {
    if (filtersValue.value.loa && e.loa !== filtersValue.value.loa.id) return false
    //if (filtersValue.value.unidade && e.unidade_orcamentaria?.id !== filtersValue.value.unidade.id) return false
    //if (filtersValue.value.entidade && e.entidade?.id !== filtersValue.value.entidade.id) return false
    return true
  })
})

const ajustesList = computed(() => {
  const ajustes = Object.values(syncStore.data_cache?.loa_registroajusteloa || {})
  return ajustes.filter(a => {
    if (filtersValue.value.loa && a.oficio_ajuste_loa__loa !== filtersValue.value.loa.id) return false
    return true
  })
})

watch(
  () => filtersValue.value,
  (nf) => {
    console.log('Filters changed:', nf)
    Promise.all([
      syncStore.fetchSync({
        app: 'loa',
        model: 'emendaloa',
        params: {
          loa: nf.loa?.id,
          unidade: nf.unidade?.id || '',
          entidade: nf.entidade?.id || ''
        }
      }),
      syncStore.fetchSync({
        app: 'loa',
        model: 'registroajusteloa',
        params: {
          oficio_ajuste_loa__loa: nf.loa?.id
        }
      })
    ]).then(() => {
      // Lógica adicional após o fetch, se necessário
    })
  },
  { deep: true }
)

onMounted(async () => {
  EventBus.emit('side:close-sideleft')
  EventBus.emit('side:close-sideright')
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})

</script>

<style lang="scss" scoped>
.loa-pcl {
  &:fullscreen {
    // background: var(--bs-body-bg);
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
