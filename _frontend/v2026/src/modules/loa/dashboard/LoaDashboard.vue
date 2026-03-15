<template>
  <div
    ref="dashboardEl"
    class="loa-dashboard"
  >
    <div class="header-area">
      <div class="inner-header d-flex flex-column gap-2">
        <div class="d-flex flex-column flex-md-row align-items-start align-items-md-center justify-content-between gap-2">
          <div class="d-flex gap-2 flex-column">
            <h3 class="dashboard-title mb-0">
              <FontAwesomeIcon
                icon="landmark"
                class="me-2 title-icon"
              />
              Orçamento Impositivo - Jataí - GO
            </h3>
            <AnoSelector
              v-model="anosSelecionados"
              :items="loaComOrcImp"
            />
          </div>
          <Totalizadores :totais="totaisSelecionados" />

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
    <div class="cards" />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref, watch } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import AnoSelector from './AnoSelector.vue'
import Totalizadores from './Totalizadores.vue'

const syncStore = useSyncStore()
const anosSelecionados = ref([])

const dashboardEl = ref(null)
const isFullscreen = ref(false)

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    dashboardEl.value?.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const onFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  syncLoa()
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})

const loaComOrcImp = computed(() => {
  if (syncStore.data_cache?.loa_loa) {
    return _.orderBy(
      _.filter(
        Object.values(syncStore.data_cache.loa_loa),
        (loa) => {
          return loa.disp_total > 0
        }
      ),
      ['ano', 'disp_total'],
      ['desc', 'desc']
    )
  }
  return []
})

const totaisSelecionados = computed(() => {
  if (!anosSelecionados.value.length || !loaComOrcImp.value.length) return null
  const selecionadas = loaComOrcImp.value.filter((loa) => anosSelecionados.value.includes(loa.ano))
  return {
    disp_total: selecionadas.reduce((sum, loa) => sum + Number(loa.disp_total), 0),
    disp_saude: selecionadas.reduce((sum, loa) => sum + Number(loa.disp_saude), 0),
    disp_diversos: selecionadas.reduce((sum, loa) => sum + Number(loa.disp_diversos), 0)
  }
})

const loasSelecionados = computed(() => {
  return loaComOrcImp.value.filter((loa) => anosSelecionados.value.includes(loa.ano))
})

watch(loaComOrcImp, (items) => {
  if (items.length && !anosSelecionados.value.length) {
    anosSelecionados.value = [items[0].ano]
  }
}, { immediate: true })

const syncLoa = async () => {
  syncStore.fetchSync({
    app: 'loa',
    model: 'loa',
    params: {
      get_all: true
    }
  })
}
</script>

<style lang="scss" scoped>
.loa-dashboard {
  &:fullscreen {
    background: var(--bs-body-bg);
    overflow: auto;
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

    [data-bs-theme="dark"] & {
       background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    }
    // border: 1px solid var(--bs-border-color);
    // box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);

  }
}

.dashboard-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--bs-body-color);
  white-space: nowrap;

  .title-icon {
    color: var(--bs-primary);
  }
}
</style>
