<template>
  <div
    ref="rootEl"
    class="pcl-detalhe-ajuste"
  >
    <div class="emenda-card card border-0 shadow-sm mb-3">
      <!-- CABEÇALHO -->
      <div class="card-header bg-body border-bottom-0 pb-0">
        <div class="d-flex align-items-start flex-wrap">
          <div
            class="emenda-parlamentares-fotos d-flex flex-wrap me-3 mb-1"
            v-if="registro.parlamentares_valor && registro.parlamentares_valor.length"
          >
            <a
              v-for="pId in registro.parlamentares_valor"
              :key="typeof pId === 'object' ? pId.id : pId"
              class="emenda-avatar"
              :title="parlamentarNome(pId)"
              href="#"
              @click.prevent="emit('filter-parlamentar', parlamentarObj(pId))"
            >
              <img
                :src="fotoThumb(parlamentarFoto(pId))"
                :alt="parlamentarNome(pId)"
              >
            </a>
          </div>

          <div class="flex-grow-1">
            <h4 class="mb-1 fw-bold">
              <a
                :href="registro.link_detail_backend"
                target="_blank"
              >
                {{ oficioLabel }}
                <FontAwesomeIcon
                  icon="external-link-alt"
                  size="sm"
                  class="ms-1 text-muted"
                />
              </a>
            </h4>
            <div class="mb-2">
              <span class="badge me-1 text-bg-warning">Registro de Ajuste</span>
              <span :class="['badge', `text-bg-${situacaoVariant(registro.fase_prestacao_contas)}`]">
                {{ situacaoLabel(registro.fase_prestacao_contas) }}
              </span>
            </div>
          </div>

          <div
            v-if="registro.str_valor"
            class="text-center ms-auto p-2 me-3 rounded"
          >
            <span class="emenda-valor fw-bold text-primary">
              R$ {{ registro.str_valor }}
            </span>
            <br>
            <small class="text-muted">Valor do Ajuste</small>
          </div>
        </div>
      </div>

      <hr class="my-0">

      <!-- DADOS PRINCIPAIS -->
      <div class="card-body pt-2 pb-2">
        <div class="row">
          <div class="col-md-12">
            <small
              class="d-block text-muted"
              v-if="unidadeObj"
            >
              <strong><FontAwesomeIcon
                icon="building"
                class="me-1"
              />Unidade Orçamentária:</strong>
              <button
                class="btn btn-link btn-sm p-0 align-baseline"
                @click="emit('filter-unidade', unidadeObj)"
              >{{ unidadeObj.__str__ }}</button>
            </small>
            <small
              class="d-block text-muted"
              v-if="emendasLoaList.length"
            >
              <strong>Emendas vinculadas:</strong>
              <template
                v-for="(em, idx) in emendasLoaList"
                :key="`emenda_${em.id}_${idx}`"
              >
                <button
                  class="btn btn-link btn-sm p-0 align-baseline"
                  @click="emit('search-emenda', em.text)"
                >{{ em.text }}</button><span v-if="idx < emendasLoaList.length - 1">, </span>
              </template>
            </small>
          </div>
        </div>

        <div
          class="mt-2 p-2 bg-body-secondary rounded border"
          v-if="registro.descricao"
        >
          <small class="text-muted">
            <strong>Descrição:</strong>
            {{ registro.descricao }}
          </small>
        </div>
      </div>

      <!-- ABAS -->
      <div
        class="bg-body p-0 mt-2"
        v-if="prestacaoItems && prestacaoItems.length"
      >
        <ul
          class="nav nav-tabs emenda-tabs"
          role="tablist"
        >
          <li class="nav-item">
            <button
              class="nav-link active"
              type="button"
            >
              Prestação de Contas
              <span class="badge rounded-pill text-bg-secondary ms-1">{{ prestacaoItems.length }}</span>
            </button>
          </li>
        </ul>
        <PclTabPrestacao
          :items="prestacaoItems"
          :registro="registro"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import { situacaoLabel, situacaoVariant, fotoThumb } from './utils/pcl-helpers'
import PclTabPrestacao from './tabs/PclTabPrestacao.vue'

const syncStore = useSyncStore()

const props = defineProps({
  registro: { type: Object, required: true }
})

const emit = defineEmits(['filter-unidade', 'filter-parlamentar', 'search-emenda'])

const rootEl = ref(null)
const visible = ref(false)
const prestacaoItems = ref(null)

let observer = null

const oficioLabel = computed(() => {
  const oficio = props.registro.oficio_ajuste_loa
  if (!oficio) return 'Registro de Ajuste'
  if (typeof oficio === 'object') return oficio.__str__ || 'Registro de Ajuste'
  const cached = syncStore.data_cache?.loa_oficioajusteloa?.[oficio]
  return cached?.__str__ || 'Registro de Ajuste'
})

const unidadeObj = computed(() => {
  const uid = props.registro.unidade
  if (!uid) return null
  if (typeof uid === 'object') return uid
  return syncStore.data_cache?.loa_unidadeorcamentaria?.[uid] || null
})

function parlamentarObj (pId) {
  if (typeof pId === 'object') return pId
  return syncStore.data_cache?.parlamentares_parlamentar?.[pId] || { id: pId }
}

function parlamentarNome (pId) {
  const p = parlamentarObj(pId)
  return p.__str__ || p.nome_parlamentar || ''
}

function parlamentarFoto (pId) {
  const p = parlamentarObj(pId)
  return p.fotografia || ''
}

const emendasLoaList = computed(() => {
  if (!props.registro.emendaloa) return []
  const lista = Array.isArray(props.registro.emendaloa)
    ? props.registro.emendaloa
    : [props.registro.emendaloa]
  return lista.map(e => {
    if (typeof e === 'object') {
      return {
        id: e.id,
        pkloa: e.loa,
        text: (e.__str__ || '').split('-')[0].trim()
      }
    }
    const cached = syncStore.data_cache?.loa_emendaloa?.[e]
    return {
      id: e,
      text: cached ? (cached.__str__ || '').split('-')[0].trim() : `Emenda #${e}`
    }
  }).filter(e => e.text)
})

async function fetchTabData (registro) {
  prestacaoItems.value = null

  const cache = await syncStore.fetchSync({
    app: 'loa',
    model: 'prestacaocontaregistro',
    params: {
      registro_ajuste: registro.id,
      get_all: 'True',
      expand: 'prestacao_conta;registro_ajuste'
    }
  })
  prestacaoItems.value = cache
    ? Object.values(cache).filter(p => p.registro_ajuste === registro.id || p.registro_ajuste?.id === registro.id)
    : []
}

watch(() => props.registro, (reg) => {
  if (reg && visible.value) fetchTabData(reg)
}, { immediate: true })

watch(visible, (val) => {
  if (val && props.registro) fetchTabData(props.registro)
})

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      visible.value = true
      observer.disconnect()
    }
  }, { rootMargin: '200px' })
  if (rootEl.value) observer.observe(rootEl.value)
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<style lang="scss" scoped>
.pcl-detalhe-ajuste :deep() {
  .emenda-card {
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.12) !important;
    }

    .card-header {
      padding: 1rem;
    }

    .emenda-parlamentares-fotos {
      .emenda-avatar {
        display: inline-block;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid var(--bs-border-color);
        transition: border-color 0.2s, transform 0.15s ease;
        margin-right: -10px;

        &:hover {
          border-color: var(--bs-primary);
          transform: translateY(-2px) scale(1.1);
          z-index: 2;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }
    }

    h4 a {
      color: inherit;
      text-decoration: none;

      &:hover {
        color: var(--bs-primary);
        text-decoration: none;
      }
    }

    .emenda-valor {
      font-size: 1.3rem;
      white-space: nowrap;
    }
  }

  .nav-tabs {
    padding: 0 0.5rem;

    .nav-link {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--bs-secondary-color);
      padding: 0.4rem 0.75rem;

      &.active {
        color: var(--bs-body-color);
      }
    }
  }
}

@media (max-width: 991.98px) {
  .pcl-detalhe-ajuste :deep() {
    .emenda-card .card-header .ms-auto {
      flex: 0 0 100%;
      margin-left: 0 !important;
      margin-right: 0 !important;
      margin-top: 0.5rem;
      text-align: center !important;
    }
  }
}

@media (max-width: 767.98px) {
  .pcl-detalhe-ajuste :deep() {
    .emenda-card {
      .card-header { padding: 0.75rem; }
      h4 { font-size: 1rem; }
      .emenda-parlamentares-fotos .emenda-avatar { width: 38px; height: 38px; }
      .emenda-valor { font-size: 1.05rem; }
    }
    .nav-tabs .nav-link { font-size: 0.75rem; padding: 0.3rem 0.5rem; }
  }
}

@media (max-width: 425px) {
  .pcl-detalhe-ajuste :deep() {
    .emenda-card {
      .card-header { padding: 0.5rem; }
      h4 { font-size: 0.9rem; }
      .emenda-parlamentares-fotos .emenda-avatar { width: 32px; height: 32px; }
      .emenda-valor { font-size: 0.95rem; }
      .card-body { padding: 0.5rem; }
    }
    .nav-tabs .nav-link { font-size: 0.7rem; padding: 0.25rem 0.4rem; }
  }
}
</style>
