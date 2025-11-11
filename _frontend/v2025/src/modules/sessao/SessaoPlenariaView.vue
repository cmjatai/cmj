<template>
  <div
    :key="`sessao-plenaria-view-${sessaoId}`"
    class="sessao-plenaria-view"
  >
    <small v-if="sessao">
      {{ sessao.__str__ }}
    </small>
    <div
      class="sessao-plenaria-content"
      v-if="sessao"
    >
      <div
        v-if="textoAbertura.length > 0"
        @click="toggleRitoOpened"
        :class="['sessao-plenaria-textos', ritoOpened ? 'open' : 'closed']"

      >
        <div v-html="ritoOpened ? textoAbertura[0].conteudo : 'Visualizar o Rito...'" />
      </div>
      <ExpedienteMateriaList
        :sessao="sessao"
        @resync="handleResync"
      />
      <div
        v-if="textoTribuna.length > 0"
        @click="toggleRitoOpened"
        :class="['sessao-plenaria-textos', ritoOpened ? 'open' : 'closed']"
      >
        <div v-html="ritoOpened ? textoTribuna[0].conteudo : 'Visualizar o Rito...'" />
      </div>
      <OrdemDiaList
        :sessao="sessao"
        @resync="handleResync"
      />
      <div
        v-if="textoFechamento.length > 0"
        @click="toggleRitoOpened"
        :class="['sessao-plenaria-textos', ritoOpened ? 'open' : 'closed']"
      >
        <div v-html="ritoOpened ? textoFechamento[0].conteudo : 'Visualizar o Rito...'" />
      </div>
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted, computed, inject } from 'vue'
import ExpedienteMateriaList from './ExpedienteMateriaList.vue'
import OrdemDiaList from './OrdemDiaList.vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const EventBus = inject('EventBus')

const sessaoId = ref(Number(route.params.id) || 0)
const ritoOpened = ref(false)
const sessao = computed(() => {
  return syncStore.data_cache?.sessao_sessaoplenaria?.[sessaoId.value]
})

onMounted(() => {
  // Lógica de inicialização, se necessário
  syncStore.fetchSync({
    app: 'sessao',
    model: 'sessaoplenaria',
    id: sessaoId.value,
    params: {
    }, force_fetch: true
  }).then(() => {
    // Sessão carregada
    handleResync({force_fetch_materias: false})
  })
})
const textoAbertura = computed(() => {
  return Object.values(syncStore.data_cache?.sessao_expedientesessao || {}).filter(
    exp => exp.sessao_plenaria === sessaoId.value && exp.tipo === 1
  )
})

const textoTribuna = computed(() => {
  return Object.values(syncStore.data_cache?.sessao_expedientesessao || {}).filter(
    exp => exp.sessao_plenaria === sessaoId.value && exp.tipo === 3
  )
})

const textoFechamento = computed(() => {
  return Object.values(syncStore.data_cache?.sessao_expedientesessao || {}).filter(
    exp => exp.sessao_plenaria === sessaoId.value && exp.tipo === 4
  )
})

EventBus.on('rito-toggle', () => {
  ritoOpened.value = !ritoOpened.value
})
const toggleRitoOpened = () => {
  EventBus.emit('rito-toggle')
}

const handleResync = ({force_fetch_materias = true}) => {
  syncStore.invalidateDataCache([
    'sessao'
  ], [
    'expedientemateria',
    'ordemdia'
  ])
  syncStore.fetchSync({
    app: 'sessao',
    model: 'expedientesessao',
    params: {
      sessao_plenaria: sessaoId.value,
      get_all: 'True'
    }
  })
  syncStore.fetchSync({
    app: 'sessao',
    model: 'expedientemateria',
    params: {
      sessao_plenaria: sessaoId.value,
      expand: 'materia.autores.tipo;tramitacao',
      exclude: 'materia.metadata',
      get_all: 'True'
    }
  })
  .then(() => {
    return syncStore.fetchSync({
      app: 'sessao',
      model: 'ordemdia',
      params: {
        sessao_plenaria: sessaoId.value,
        expand: 'materia.autores.tipo;tramitacao',
        exclude: 'materia.metadata',
        get_all: 'True'
      }
    })
  })
  .then(() => {
    const materiasDaSessao = new Set()
    // Coleta IDs de matérias do expediente
    const allExpedientes = syncStore.data_cache?.sessao_expedientemateria || {}
    Object.values(allExpedientes).forEach(exp => {
      if (exp.sessao_plenaria === sessaoId.value) {
        materiasDaSessao.add(exp.materia)
      }
    })
    // Coleta IDs de matérias da ordem do dia
    const allOrdemDias = syncStore.data_cache?.sessao_ordemdia || {}
    Object.values(allOrdemDias).forEach(ordem => {
      if (ordem.sessao_plenaria === sessaoId.value) {
        materiasDaSessao.add(ordem.materia)
      }
    })
    // Sincroniza matérias relacionadas
    if (materiasDaSessao.size > 0) {
      syncStore.fetchSync(
        {
          app: 'materia',
          model: 'materialegislativa',
          params: {
            id__in: Array.from(materiasDaSessao),
            exclude: 'metadata',
            get_all: 'True'
          },
          force_fetch: force_fetch_materias
        }
      )
      .then(() => {
        return syncStore.fetchSync({
          app: 'materia',
          model: 'documentoacessorio',
          params: {
            materia__in: Array.from(materiasDaSessao),
            exclude: 'metadata',
            get_all: 'True'
          }
        })
      })
      .then(() => {
        return syncStore.fetchSync({
          app: 'norma',
          model: 'legislacaocitada',
          params: {
            materia__in: Array.from(materiasDaSessao),
            exclude: 'metadata',
            get_all: 'True'
          }
        })
      })
    }
  })
}

</script>
<style lang="scss">
.sessao-plenaria-view {
  .sessao-plenaria-textos {
    position: relative;
    display: inline-block;
    margin: 1em 1em 0;
    padding: 1em;
    background-color: var(--bs-body-bg);
    color: var(--bs-secondary);
    border: 1px solid var(--bs-border-color);
    font-family: var(--bs-font-monospace);
    white-space: pre-wrap;
    line-height: 1.5;
    p {
      margin: 0;
    }
    &.closed {
      font-size: 80%;
      padding: 0.1em 1em 0.1em 0.5em;
      overflow: hidden;
      cursor: pointer;
      opacity: 0.8;
      &::after {
        content: " ▼";
        position: absolute;
        bottom: 0.3em;
        right: 0.5em;
        font-size: 0.8em;
        color: var(--bs-secondary);
      }
    }
  }
}
</style>
