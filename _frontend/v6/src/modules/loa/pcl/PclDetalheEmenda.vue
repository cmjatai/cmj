<template>
  <div
    ref="rootEl"
    class="pcl-detalhe-emenda"
  >
    <div :class="['emenda-card', 'card', 'shadow-sm', 'mb-3', emendaTipoClass]">
      <!-- CABEÇALHO -->
      <div class="card-header border-bottom-0 pb-0">
        <div class="d-flex align-items-start flex-wrap">
          <div
            class="emenda-parlamentares-fotos d-flex flex-wrap me-3 mb-1"
            v-if="registro.parlamentares && registro.parlamentares.length"
          >
            <a
              v-for="pId in registro.parlamentares"
              :key="pId"
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
            <h3 class="mb-1 fw-bold text-wrap text-primary">
              <a
                :href="registro.link_detail_backend"
                target="_blank"
              >
                {{ tituloRegistro }}
                <FontAwesomeIcon
                  icon="external-link-alt"
                  size="sm"
                  class="ms-1 text-muted"
                />
              </a>
            </h3>
            <div class="mb-2">
              <span :class="['badge', 'me-1', `text-bg-${tipoVariant(registro.tipo)}`]">
                <FontAwesomeIcon
                  :icon="tipoIcon"
                  class="me-1"
                />{{ tipoLabel(registro.tipo) }}
              </span>
              <span :class="['badge', 'me-1', `text-bg-${faseVariant(registro.fase)}`]">
                {{ faseLabel(registro.fase) }}
              </span>
            </div>
          </div>

          <div class="emenda-valor-group d-flex text-center ms-auto p-2 me-3 rounded">
            <div :class="{ 'zoom08': hasAjustes }">
              <span class="emenda-valor fw-bold text-primary">
                R$ {{ registro.str_valor || registro.str_valor_computado }}
              </span>
              <br>
              <small class="text-muted">Valor Original da Emenda</small>
            </div>
            <div
              class="valor-computado"
              v-if="hasAjustes || !registro.valor_computado"
            >
              <span class="emenda-valor fw-bold text-success">
                R$ {{ registro.str_valor_computado }}
              </span>
              <br>
              <small
                class="text-muted"
                v-if="registro.valor_computado"
              >Valor Final após Ajustes</small>
              <small
                class="text-muted"
                v-else
              >Emenda Redefinida nos Ajustes</small>
            </div>
          </div>
        </div>
      </div>

      <hr class="my-0 mx-2">

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
              />Unidade Orçamentária: </strong>
              <button
                class="btn btn-link btn-sm p-0 align-baseline"
                @click="emit('filter-unidade', unidadeObj)"
              >{{ unidadeObj.__str__ }}</button>
            </small>
            <template v-if="entidadeObj">
              <small
                class="text-muted"
                v-if="entidadeObj.nome_fantasia"
              >
                <strong><FontAwesomeIcon
                  icon="hand-holding-heart"
                  class="me-1"
                />Beneficiário: </strong>
                <button
                  class="btn btn-link btn-sm p-0 align-baseline"
                  @click="emit('filter-entidade', entidadeObj)"
                >{{ entidadeObj.nome_fantasia }}</button>
              </small>
              <small
                class="text-muted"
                v-if="entidadeObj.cnes"
              >
                <strong> - CNES:</strong> {{ entidadeObj.cnes }}
              </small>
              <small
                class="text-muted"
                v-else-if="cpfcnpjLimpo(entidadeObj.cpfcnpj)"
              >
                <strong> - CPF/CNPJ:</strong> {{ cpfcnpjLimpo(entidadeObj.cpfcnpj) }}
              </small>
            </template>
          </div>
        </div>

        <div
          class="mt-2 p-2 bg-body-secondary rounded border"
          v-if="registro.ementa_format"
        >
          <small class="text-muted">
            <strong>Objeto Inicial:</strong>
            <span :class="[hasAjustes && registro.valor_computado ? 'text-decoration-line-through' : '']">
              {{ registro.ementa_format }}
            </span>
          </small>
          <template v-if="hasAjustes">
            <hr class="my-2">
            <small class="badge text-bg-warning text-wrap">
              <strong>Atenção!</strong>
            </small>
            <small class="text-muted mt-1">
              Esta emenda possui ajustes técnicos cadastrados.
              Verifique a aba "Ajustes Técnicos" para mais detalhes.
            </small>
          </template>
        </div>
      </div>

      <!-- ABAS -->
      <div
        class="bg-body p-0 mt-2"
        v-if="registro.tipo !== 0"
      >
        <ul
          class="nav nav-tabs nav-fill emenda-tabs"
          role="tablist"
        >
          <li
            v-for="(tab, index) in orderedTabs"
            :key="tab.key"
            class="nav-item"
          >
            <button
              class="nav-link"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
              type="button"
            >
              {{ tab.title }}
              <span
                v-if="tab.count !== null"
                class="badge rounded-pill text-bg-secondary ms-1"
              >{{ tab.count }}</span>
            </button>
          </li>
        </ul>
        <div class="tab-content">
          <div v-if="activeTab === 'prestacao'">
            <PclTabPrestacao
              :items="prestacaoItems"
              :registro="registro"
            />
          </div>
          <div v-if="activeTab === 'ajustes'">
            <PclTabAjustes :items="ajustesItems" />
          </div>
          <div v-if="activeTab === 'tramitacoes'">
            <PclTabTramitacoes :items="tramitacoesItems" />
          </div>
          <div v-if="activeTab === 'documentos'">
            <PclTabDocumentos :items="documentosItems" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import {
  registroBadgeLabel,
  faseVariant,
  faseLabel,
  tipoVariant,
  tipoLabel,
  fotoThumb
} from './utils/pcl-helpers'
import PclTabPrestacao from './tabs/PclTabPrestacao.vue'
import PclTabAjustes from './tabs/PclTabAjustes.vue'
import PclTabDocumentos from './tabs/PclTabDocumentos.vue'
import PclTabTramitacoes from './tabs/PclTabTramitacoes.vue'

const syncStore = useSyncStore()

const props = defineProps({
  registro: { type: Object, required: true }
})

const emit = defineEmits(['filter-unidade', 'filter-entidade', 'filter-parlamentar'])

const rootEl = ref(null)
const visible = ref(false)
const activeTab = ref('prestacao')
const prestacaoItems = ref(null)
const ajustesItems = ref(null)
const documentosItems = ref(null)
const tramitacoesItems = ref(null)

let observer = null

const TIPO_ICONS = { 0: 'pen-fancy', 10: 'heartbeat', 99: 'th-large' }

const tipoIcon = computed(() => TIPO_ICONS[props.registro.tipo] || 'file-alt')

const unidadeObj = computed(() => {
  const uid = props.registro.unidade
  if (!uid) return null
  if (typeof uid === 'object') return uid
  return syncStore.data_cache?.loa_unidadeorcamentaria?.[uid] || null
})

const entidadeObj = computed(() => {
  const eid = props.registro.entidade
  if (!eid) return null
  if (typeof eid === 'object') return eid
  return syncStore.data_cache?.loa_entidade?.[eid] || null
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

const tituloRegistro = computed(() => {
  if (props.registro.materia) {
    const mId = typeof props.registro.materia === 'object' ? props.registro.materia.id : props.registro.materia
    const m = syncStore.data_cache?.materia_materialegislativa?.[mId] || props.registro.materia
    if (typeof m === 'object') {
      if (m.tipo && (m.tipo.sigla || m.tipo.__str__)) {
        const sigla = m.tipo.sigla || ''
        const tipoNome = m.tipo.__str__ || m.tipo.descricao || ''
        const num = String(m.numero || '').padStart(3, '0')
        return `${sigla} ${num}/${m.ano} - ${tipoNome}`
      }
      return m.epigrafe || m.__str__ || props.registro.epigrafe_short || 'Emenda em Elaboração'
    }
  }
  return registroBadgeLabel(props.registro)
})

const hasAjustes = computed(() => {
  if (props.registro.has_ajustes !== undefined) return props.registro.has_ajustes
  return Array.isArray(ajustesItems.value) && ajustesItems.value.length > 0
})

const orderedTabs = computed(() => {
  const tabs = []
  tabs.push({
    key: 'prestacao',
    title: 'Prestação de Contas',
    count: prestacaoItems.value?.length ?? null,
    hasData: Array.isArray(prestacaoItems.value) && prestacaoItems.value.length > 0
  })
  tabs.push({
    key: 'ajustes',
    title: 'Ajustes Técnicos',
    count: ajustesItems.value?.length ?? null,
    hasData: Array.isArray(ajustesItems.value) && ajustesItems.value.length > 0
  })
  tabs.sort((a, b) => (b.hasData ? 1 : 0) - (a.hasData ? 1 : 0))

  if (props.registro.materia) {
    tabs.push({
      key: 'tramitacoes',
      title: 'Tramitações',
      count: tramitacoesItems.value?.length ?? null,
      hasData: Array.isArray(tramitacoesItems.value) && tramitacoesItems.value.length > 0
    })
    tabs.push({
      key: 'documentos',
      title: 'Documentos Acessórios',
      count: documentosItems.value?.length ?? null,
      hasData: Array.isArray(documentosItems.value) && documentosItems.value.length > 0
    })
  }
  return tabs
})

function cpfcnpjLimpo (val) {
  if (!val) return ''
  return val.replace(/[0\s]/g, '') ? val.trim() : ''
}

async function fetchTabData (registro) {
  prestacaoItems.value = null
  ajustesItems.value = null
  documentosItems.value = null
  tramitacoesItems.value = null

  const prestacaoCache = await syncStore.fetchSync({
    app: 'loa',
    model: 'prestacaocontaregistro',
    params: {
      emendaloa: registro.id,
      get_all: 'True',
      expand: 'prestacao_conta;registro_ajuste'
    }
  })
  prestacaoItems.value = prestacaoCache ? Object.values(prestacaoCache) : []

  const ajustesCache = await syncStore.fetchSync({
    app: 'loa',
    model: 'registroajusteloa',
    params: {
      emendaloa: registro.id,
      get_all: 'True',
      expand: 'oficio_ajuste_loa;unidade;materia'
    }
  })
  ajustesItems.value = ajustesCache ? Object.values(ajustesCache).filter(a => a.emendaloa === registro.id || a.emendaloa?.id === registro.id) : []

  if (registro.materia) {
    const materiaId = typeof registro.materia === 'object' ? registro.materia.id : registro.materia

    const docsCache = await syncStore.fetchSync({
      app: 'materia',
      model: 'documentoacessorio',
      params: {
        materia: materiaId,
        get_all: 'True',
        expand: 'tipo'
      }
    })
    documentosItems.value = docsCache ? Object.values(docsCache).filter(d => d.materia === materiaId || d.materia?.id === materiaId) : []

    const tramCache = await syncStore.fetchSync({
      app: 'materia',
      model: 'tramitacao',
      params: {
        materia: materiaId,
        get_all: 'True',
        expand: 'unidade_tramitacao_local;unidade_tramitacao_destino;status',
        include: 'status.id,__str__;unidade_tramitacao_local.id,__str__;unidade_tramitacao_destino.id,__str__'
      }
    })
    tramitacoesItems.value = tramCache ? Object.values(tramCache).filter(t => t.materia === materiaId || t.materia?.id === materiaId) : []
  }

  // set activeTab to first tab with data
  if (orderedTabs.value.length) {
    activeTab.value = orderedTabs.value[0].key
  }
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
.pcl-detalhe-emenda :deep() {
  .emenda-card {
    transition: box-shadow 0.2s;
    border: 0;
    border-left: 2px solid transparent;

    &.emenda-tipo-info { border-left-color: var(--bs-info); }
    &.emenda-tipo-success { border-left-color: var(--bs-success); }
    &.emenda-tipo-warning { border-left-color: var(--bs-warning); }
    &.emenda-tipo-light { border-left-color: var(--bs-border-color); }

    &:hover {
      box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.12) !important;
    }

    .card-header {
      padding: 1rem;
      background-color: var(--bs-body-bg);
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

    .emenda-valor-group {
      display: flex;
      align-items: center;
      gap: 3rem;
      line-height: 1;
      margin-bottom: 0.5rem;

      .emenda-valor {
        font-size: 1.3rem;
        white-space: nowrap;
      }
    }

    .zoom08 {
      transform: scale(0.8);
    }

    h3 a {
      color: inherit;
      text-decoration: none;

      &:hover {
        color: var(--bs-primary);
        text-decoration: none;
      }
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
  .pcl-detalhe-emenda :deep() {
    .emenda-card .emenda-valor-group {
      flex: 0 0 100%;
      margin-left: 0 !important;
      margin-right: 0 !important;
      margin-top: 0.5rem;
      justify-content: flex-start;
      gap: 1.5rem;
      text-align: left;
    }
  }
}

@media (max-width: 767.98px) {
  .pcl-detalhe-emenda :deep() {
    .emenda-card {
      .card-header { padding: 0.75rem; }
      h3 { font-size: 1rem; }
      .emenda-parlamentares-fotos .emenda-avatar { width: 38px; height: 38px; }
      .emenda-valor-group .emenda-valor { font-size: 1.05rem; }
    }
    .nav-tabs .nav-link { font-size: 0.75rem; padding: 0.3rem 0.5rem; }
  }
}

@media (max-width: 425px) {
  .pcl-detalhe-emenda :deep() {
    .emenda-card {
      .card-header { padding: 0.5rem; }
      h3 { font-size: 0.9rem; }
      .emenda-parlamentares-fotos .emenda-avatar { width: 32px; height: 32px; }
      .emenda-valor-group {
        flex-direction: column;
        gap: 0.5rem !important;
        .emenda-valor { font-size: 0.95rem; }
      }
      .card-body { padding: 0.5rem; }
    }
    .nav-tabs .nav-link { font-size: 0.7rem; padding: 0.25rem 0.4rem; }
  }
}
</style>
