<template>
  <div
    class="painelset-painel"
    :style="painel?.styles.container || {}"
  >
    <div
      v-if="painel?.config?.displayTitle"
      class="painel-titulo"
      :style="painel?.styles.title || {}"
    >
      {{ painel?.name }}
    </div>
    <div
      v-if="painelVisaoSelected"
      class="inner-painelset-painel"
      :style="painel?.styles.inner || {}"
    >
      <PainelVisao
        :key="`painelvisao-${painelVisaoSelected.id}`"
        :painel-id="painelId"
        :painelvisao-selected="painelVisaoSelected"
      />
      <div class="actions">
        <div
          class="btn-group btn-group-sm"
          role="group"
          aria-label="Visões do Painel">
          <button
            v-for="(pv, index) in painelVisaoList"
            :key="`${pv.id}_${index}`"
            :class="{ active: pv.id === painelVisaoSelected }"
            class="btn btn-primary"
            @click="trocarVisao(pv.id)"
          >
            {{ pv.position }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="false">
      <br><br>
      &nbsp;
      <button @click="visaoAtiva()">Visao Ativa</button>
      <br><br>
      <button v-for="(pv, index) in painelVisaoList" :key="index" @click="ativarVisao(pv.id)">Ativar {{ pv.id }}</button>
      <br><br>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useRouter, useRoute } from 'vue-router'
import { ref, defineProps, computed, watch } from 'vue'
import Resource from '~@/utils/resources'

import PainelVisao from './PainelVisao.vue'

const syncStore = useSyncStore()
const router = useRouter()
const route = useRoute()

syncStore.registerModels('painelset', [
  'painel',
  'painelvisao',
  'evento'
])

syncStore.registerModels('sessao', [
  'sessaoplenaria'
])

syncStore.registerModels('materia', [
  'materialegislativa'
])

const props = defineProps({
  painelId: {
    type: String,
    default: '0'
  }
})

const routePainelId = ref(Number(route.params.painelId) || 0)
const painelId = ref(Number(props.painelId) || routePainelId.value || 0 )

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[painelId.value] || null
})

const painelVisaoList = computed(() => {
  return _.orderBy(
    _.filter(syncStore.data_cache.painelset_painelvisao, { painel: painelId.value } ) || [],
    ['position'],
    ['asc']
  )
})

const painelVisaoSelected = ref(null)

watch(
  () => props.painelId,
  (newPainelId) => {
    if (newPainelId !== painelId.value) {
      painelId.value = newPainelId
      syncPainel()
    }
  }
)

watch(
  () => painelId.value,
  (newPainelId) => {
    if (newPainelId) {
      syncPainelVisaoList(newPainelId)
    }
  }
)

const syncPainelVisaoList = async (painelId) => {
  await syncStore
    .fetchSync({
      app: 'painelset',
      model: 'painelvisao',
      params: {
        painel: painelId
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        const painelVisaoAtivo = response.data.results.find(
          (pv) => pv.active === true
        )
        if (painelVisaoAtivo) {
          painelVisaoSelected.value = painelVisaoAtivo.id
        } else {
          painelVisaoSelected.value = response.data.results[0].id
        }
      }
    })
}

const syncPainel = async () => {
  if (painelId.value) {
    syncStore
      .fetchSync({
        app: 'painelset',
        model: 'painel',
        id: painelId.value
      })
      .then(() => {
        syncPainelVisaoList(painelId.value)
      })
      .catch((error) => {
        // router push to 404
        console.error('Error fetching painel:', error)
        router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
      })
  } else {
    syncStore
      .fetchSync({
        app: 'painelset',
        model: 'evento',
        params: {
          end_real__isnull: true,
          start_real__isnull: false
        }
      })
      .then((response) => {
        if (response && response.data.results.length > 0) {
          const evento = response.data.results[0]
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'painel',
              params: {
                evento: evento.id
              }
            })
            .then((painelResponse) => {
              if (painelResponse && painelResponse.data.results.length > 0) {
                const firstPainel = painelResponse.data.results[0]
                painelId.value = firstPainel.id
              } else {
                router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
              }
            })
            .catch((error) => {
              // router push to 404
              console.error('Error fetching painel for evento:', error)
              router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
            })
        } else {
          router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
        }
      })
      .catch((error) => {
        // router push to 404
        console.error('Error fetching evento:', error)
        router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
      })
  }
}

const trocarVisao = (id) => {
  painelVisaoSelected.value = id
}

const ativarVisao = (id) => {
  Resource.Utils.patchModelAction({
    app: 'painelset',
    model: 'painelvisao',
    id: id,
    action: 'activate',
    form: {}
  })
    .then(() => {
      painelVisaoSelected.value = painel.value.painelvisao_ativo_id
      syncPainelVisaoList(painelId.value)
    })
    .catch((error) => {
      console.error('Error activating painelvisao:', error)
    })
}

const visaoAtiva = () => {
  painelVisaoSelected.value = painel.value.painelvisao_ativo_id
}

syncPainel()

</script>
<style lang="scss" scoped>
.painelset-painel {
  overflow: hidden;
  display: flex;
  height: 100%;
  flex-direction: column;
  justify-content: stretch;
  .inner-painelset-painel {
    position: relative;
    display: flex;
    justify-content: stretch;
    flex: 1 1 100%;
    overflow: hidden;
    & > .actions {
      position: absolute;
      left: 0px;
      bottom: 0px;
      right: 0px;
      line-height: 1;
      text-align: right;
      .btn {
        font-size: 1em;
        padding: 0.6em;
        line-height: 1;
        border-radius: 0;
        opacity: 0.2;
      }
      &:hover {
        .btn {
          opacity: 1;
          zoom: 2;
        }
      }
    }
  }
}
</style>
