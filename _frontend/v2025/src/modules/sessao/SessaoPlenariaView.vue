<template>
  <div
    :key="`sessao-plenaria-view-${sessaoId}`"
    class="sessao-plenaria-view"
  >
    <small v-if="sessao">
      {{ sessao.__str__ }}
    </small>
    <div class="sessao-plenaria-content">
      <ExpedienteMateriaList
        :sessao="sessao"
        @resync="handleResync"
      />
      <OrdemDiaList
        :sessao="sessao"
        @resync="handleResync"
      />
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useRouter, useRoute } from 'vue-router'
import { ref, onMounted, computed } from 'vue'
import ExpedienteMateriaList from './ExpedienteMateriaList.vue'
import OrdemDiaList from './OrdemDiaList.vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const sessaoId = ref(Number(route.params.id) || 0)

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

</style>
