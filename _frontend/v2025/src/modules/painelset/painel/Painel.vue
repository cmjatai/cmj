<template>
  <div
    ref="painelsetPainel"
    class="painelset-painel"
    :style="painel?.styles.component || {}"
    @mousemove="movingSobrePainel($event)"
  >
    <div
      v-if="painel?.config?.displayTitle"
      class="painel-titulo"
      :style="painel?.styles.title || {}"
    >
      {{ painel?.name }}
    </div>
    <div
      v-if="visaoSelected"
      class="inner-painelset-painel"
      :style="painel?.styles.inner || {}"
    >
      <VisaoDePainel
        :key="`visaodepainel-${visaoSelected.id}`"
        :painel-id="painelId"
        :visaodepainel-selected="visaoSelected"
      />
      <div class="actions">
        <div
          class="btn-group btn-group-sm"
          role="group"
          aria-label="Visões do Painel"
        >
          <button
            v-for="(pv, index) in visaoList"
            :key="`${pv.id}_${index}`"
            :class="{ active: pv.id === visaoSelected }"
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
      <button @click="visaoAtiva()">
        Visao Ativa
      </button>
      <br><br>
      <button
        v-for="(pv, index) in visaoList"
        :key="index"
        @click="ativarVisao(pv.id)"
      >
        Ativar {{ pv.id }}
      </button>
      <br><br>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useRouter, useRoute } from 'vue-router'
import { ref, defineProps, computed, watch } from 'vue'
import Resource from '~@/utils/resources'

import VisaoDePainel from './VisaoDePainel.vue'

const syncStore = useSyncStore()
const router = useRouter()
const route = useRoute()

syncStore.registerModels('painelset', [
  'painel',
  'visaodepainel',
  'widget',
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

const painelsetPainel = ref(null)
const initMovingSobrePainel = ref(false)
const idTimerMovingSobrePainel = ref(null)

const movingSobrePainel = (event) => {
  if (initMovingSobrePainel.value === false) {
    initMovingSobrePainel.value = true

      _.each(painelsetPainel.value.getElementsByClassName('painelset-widget'), (element) => {
        element.classList.add('localize')
      })

    if (idTimerMovingSobrePainel.value) {
      clearTimeout(idTimerMovingSobrePainel.value)
    }
    idTimerMovingSobrePainel.value = setTimeout(() => {
      initMovingSobrePainel.value = false
      _.each(painelsetPainel.value.getElementsByClassName('painelset-widget'), (element) => {
        element.classList.remove('localize')
      })
    }, 2000)
  } else {
    clearTimeout(idTimerMovingSobrePainel.value)
    idTimerMovingSobrePainel.value = setTimeout(() => {
      initMovingSobrePainel.value = false
      _.each(painelsetPainel.value.getElementsByClassName('painelset-widget'), (element) => {
        element.classList.remove('localize')
      })
    }, 2000)
  }
}

const routePainelId = ref(Number(route.params.painelId) || 0)
const painelId = ref(Number(props.painelId) || routePainelId.value || 0 )

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[painelId.value] || null
})

const visaoList = computed(() => {
  return _.orderBy(
    _.filter(syncStore.data_cache.painelset_visaodepainel, { painel: painelId.value } ) || [],
    ['position'],
    ['asc']
  )
})

const visaoSelected = ref(null)

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
      syncVisaoList(newPainelId)
    }
  }
)

const syncVisaoList = async (painelId) => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'visaodepainel',
      params: {
        painel: painelId
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        const visaoAtiva = response.data.results.find(
          (pv) => pv.active === true
        )
        if (visaoAtiva) {
          visaoSelected.value = visaoAtiva.id
        } else {
          visaoSelected.value = response.data.results[0].id
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
        syncVisaoList(painelId.value)
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
  visaoSelected.value = id
}

const ativarVisao = (id) => {
  Resource.Utils.patchModelAction({
    app: 'painelset',
    model: 'visaodepainel',
    id: id,
    action: 'activate',
    form: {}
  })
    .then(() => {
      visaoSelected.value = painel.value.visaodepainel_ativo_id
      syncVisaoList(painelId.value)
    })
    .catch((error) => {
      console.error('Error activating visaodepainel:', error)
    })
}

const visaoAtiva = () => {
  visaoSelected.value = painel.value.visaodepainel_ativo_id
}

syncPainel()

</script>
<style lang="scss" scoped>

.painelset-painel {
  display: flex;
  flex-direction: column;
  flex: 1 1 100%;
  .inner-painelset-painel {
    display: flex;
    flex-direction: column;
    flex: 1 1 100%;
    & > .actions {
      position: absolute;
      z-index: 10000;
      bottom: 0px;
      right: 0px;
      line-height: 1;
      text-align: right;
      height: 5px;
      overflow: hidden;
      .btn {
        font-size: 1em;
        padding: 0.6em;
        line-height: 1;
        border-radius: 0;
        opacity: 1;
      }
      &:hover {
        height: auto;
        .btn {
          height: auto;
          opacity: 1;
          zoom: 2;
        }
      }
    }
  }
}

.painelset-painelold {
  overflow: hidden;
  display: none;
  height: 100%;
  flex-direction: column;
  .inner-painelset-painel {
    position: relative;
    display: flex;
    flex: 1 1 100%;
    overflow: hidden;

  }
}
</style>
