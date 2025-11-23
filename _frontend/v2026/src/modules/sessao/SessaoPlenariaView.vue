<template>
  <div
    :key="`sessao-plenaria-view-${sessaoId}`"
    class="sessao-plenaria-view"
  >
    <a
      class="sessao_link_manage"
      v-if="sessao"
      :href="sessao.link_detail_backend"
      target="_blank"
    >
      {{ sessao.__str__ }}
    </a>
    <div
      class="sessao-plenaria-content"
      v-if="sessao"
    >
      <div
        v-if="textoAbertura.length > 0"
        @click="toggleRitoOpened"
        :class="['sessao-plenaria-textos', ritoOpened ? 'open' : 'closed']"
      >
        <div v-html="ritoOpened ? textoAbertura[0].conteudo : 'Visualizar o Roteiro...'" />
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
        <div v-html="ritoOpened ? textoTribuna[0].conteudo : 'Visualizar o Roteiro...'" />
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
        <div v-html="ritoOpened ? textoFechamento[0].conteudo : 'Visualizar o Roteiro...'" />
      </div>
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useRoute } from 'vue-router'
import { ref, onMounted, computed, inject } from 'vue'
import ExpedienteMateriaList from './ExpedienteMateriaList.vue'
import OrdemDiaList from './OrdemDiaList.vue'

const syncStore = useSyncStore()
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
    handleResync(false)
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

const handleResync = (force_fetch_materias = true) => {
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

  const fetchOrdemDiaAndExpediente = async () => {
    return await Promise.all([
      syncStore.fetchSync({
        app: 'sessao',
        model: 'ordemdia',
        params: {
          sessao_plenaria: sessaoId.value,
          expand: 'materia.autores.tipo;tramitacao',
          exclude: 'materia.metadata',
          get_all: 'True'
        }
      }),
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
    ])
  }
  fetchOrdemDiaAndExpediente().then(() => {
    const ordemDiasIds = Object.values(syncStore.data_cache?.sessao_ordemdia || {}).filter(
      od => od.sessao_plenaria === sessaoId.value
    ).map(od => od.id)
    const expedientesIds = Object.values(syncStore.data_cache?.sessao_expedientemateria || {}).filter(
      em => em.sessao_plenaria === sessaoId.value
    ).map(em => em.id)

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
      syncStore.fetchSync({
        app: 'sessao',
        model: 'registroleitura',
        params: {
          materia__in: Array.from(materiasDaSessao),
          get_all: 'True'
        }
      })
      syncStore.fetchSync({
        app: 'sessao',
        model: 'registrovotacao',
        params: {
          materia__in: Array.from(materiasDaSessao),
          get_all: 'True',
          expand: 'tipo_resultado_votacao'
        }
      })
      syncStore.fetchSync({
        app: 'sessao',
        model: 'votoparlamentar',
        params: {
          ordem__in: Array.from(ordemDiasIds),
          get_all: 'True'
        }
      })
      syncStore.fetchSync({
        app: 'sessao',
        model: 'votoparlamentar',
        params: {
          expediente__in: Array.from(expedientesIds),
          get_all: 'True'
        }
      })
      syncStore.fetchSync({
        app: 'materia',
        model: 'documentoacessorio',
        params: {
          materia__in: Array.from(materiasDaSessao),
          exclude: 'metadata',
          get_all: 'True'
        }
      })
      syncStore.fetchSync({
        app: 'norma',
        model: 'legislacaocitada',
        params: {
          materia__in: Array.from(materiasDaSessao),
          exclude: 'metadata',
          get_all: 'True'
        }
      })

      syncStore.fetchSync({
        app: 'sessao',
        model: 'tiporesultadovotacao',
        params: {
          get_all: 'True'
        }
      })
      syncStore.fetchSync({
        app: 'sessao',
        model: 'sessaoplenariapresenca',
        params: {
          get_all: 'True',
          sessao_plenaria: sessaoId.value,
          expand: 'parlamentar'
        }
      })
      syncStore.fetchSync({
        app: 'sessao',
        model: 'presencaordemdia',
        params: {
          get_all: 'True',
          sessao_plenaria: sessaoId.value,
          expand: 'parlamentar'
        }
      })
    }
    EventBus.emit('ordemDiaOnLoad')
    EventBus.emit('expMatOnLoad')
  })
}

</script>
<style lang="scss">
.sessao-plenaria-view {
  .sessao_link_manage {
    display: block;
    padding: 1em;
    font-weight: bold;
    text-align: center;
    font-size: 0.66em;
    color: var(--bs-link-color);
    &:hover {
      color: var(--bs-link-hover-color);
    }
  }
  .sessao-plenaria-content {
    display: flex;
    flex-direction: column;
    gap: 0.5em;
    margin: 0em 0.5em;
  }
  .sessao-plenaria-textos {
    position: relative;
    display: inline-block;
    padding: 0.5em;
    background-color: var(--bs-body-bg);
    color: var(--bs-secondary);
    font-family: var(--bs-font-monospace);
    // white-space: pre-wrap;
    line-height: 1.3;
    font-size: 0.8em;
    border: 0;
    * {
      line-height: 1.3;
    }
    &.closed {
      border: 1px solid var(--bs-border-color);
      border-radius: 5px;
      font-size: 80%;
      padding: 0.2em 2em 0.1em 0.5em;
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
@media screen and (min-width: 768px) {
  .sessao-plenaria-view {
    .sessao_link_manage {
      font-size: 1em;
    }
    .sessao-plenaria-textos {
      font-size: 1em;
      padding: 1em;
    }

    .sessao-plenaria-content {
      display: flex;
      flex-direction: column;
      gap: 1em;
      margin: 0em;
    }
  }
}
</style>
