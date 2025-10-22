<template>
  <div
    :id="`id-painelset-painel-${painelId}`"
    ref="painelsetPainel"
    :key="`painelset-painel-${painelId}`"
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
    </div>
    <div class="painel-empty" v-else>
      <p>Não há visões de painel configuradas para este painel.</p>
      <p>Utilize o botao de adição na tela de configurações para adicionar a primeira visão do painel.</p>
    </div>
    <div
      class="actions"
      @click.stop.prevent="editmode = !editmode"
    >
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
          @click.stop.prevent="trocarVisao(pv.id)"
        >
          {{ pv.position }}
        </button>
      </div>
    </div>

    <Teleport
      v-if="editmode && editorActived"
      to="#painelset-editorarea"
      :disabled="!editorActived"
    >
      <PainelEditor
        :painel-id="painelId"
        :painel-selected="painelId"
      />
    </Teleport>

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
        @click.stop.prevent="ativarVisao(pv.id)"
      >
        Ativar {{ pv.id }}
      </button>
      <br><br>
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { activeTeleportId } from '~@/stores/TeleportStore'

import { useRouter, useRoute } from 'vue-router'
import { ref, defineProps, computed, watch, inject, nextTick, onMounted } from 'vue'

import Resource from '~@/utils/resources'

import VisaoDePainel from './VisaoDePainel.vue'
import PainelEditor from './PainelEditor.vue'

// 2. Composables
const EventBus = inject('EventBus')
const syncStore = useSyncStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

syncStore.registerModels('painelset', [
  'painel',
  'visaodepainel',
  'widget',
  'evento',
  'individuo',
  'cronometro'
])

// 3. Props & Emits
const props = defineProps({
  painelId: {
    type: String,
    default: '0'
  }
})

// 4. State & Refs
const editmode = ref(false)
const painelsetPainel = ref(null)
const initMovingSobrePainel = ref(false)
const idTimerMovingSobrePainel = ref(null)
const visaoSelected = ref(null)

const routePainelId = ref(Number(route.params.painelId) || 0)
const painelId = ref(Number(props.painelId) || routePainelId.value || 0 )

// 5. Computed Properties
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
const editorActived = computed(() => {
  return activeTeleportId.value === painelsetPainel.value.id || visaoList.value.length === 0
})

// 6. Watchers
watch(
  () => editmode.value,
  (newEditMode) => {
    if (!onChangePermission()) {
      return
    }
    if (newEditMode) {
      EventBus.emit('painelset:editorarea:close', painelsetPainel.value.id)
      nextTick(() => {
        activeTeleportId.value = painelsetPainel.value.id
      })
    }
    if (visaoList.value.length === 0) {
      activeTeleportId.value = painelsetPainel.value.id
      editmode.value = true
      return
    }
  }
)
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
watch(
  () => visaoList.value,
  (newVisaoList) => {
    if (newVisaoList.length > 0) {
      if (!visaoSelected.value || !newVisaoList.find(v => v.id === visaoSelected.value)) {
        const visaoAtiva = newVisaoList.find(
          (pv) => pv.active === true
        )
        if (visaoAtiva) {
          visaoSelected.value = visaoAtiva.id
        } else {
          visaoSelected.value = newVisaoList[0].id
        }
      }
    } else {
      visaoSelected.value = null
    }
  }
)

// 7. Events & Lifecycle Hooks
EventBus.on('painelset:editorarea:close', (sender=null) => {
  if (!onChangePermission()) {
    return
  }
  if (visaoList.value.length > 0) {
    activeTeleportId.value = null
    editmode.value = true
    return
  }
  if (sender && sender === 'force') {
    editmode.value = false
    activeTeleportId.value = null
    return
  }
  if (sender && painelsetPainel.value && sender ===  painelsetPainel.value.id) {
    return
  }
  activeTeleportId.value = null
  editmode.value = false
})

const movingSobrePainel = () => {
  if (!authStore.isAuthenticated) {
    return
  }
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

const syncPainel = async () => {
  if (painelId.value) {
    syncStore
      .fetchSync({
        app: 'painelset',
        model: 'painel',
        id: painelId.value
      })
      .then((response) => {
        if (response.data.sessao) {
          syncStore
            .fetchSync({
              app: 'sessao',
              model: 'sessaoplenaria',
              id: response.data.sessao
            })
          }
        if (response.data.evento) {
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'evento',
              id: response.data.evento
            })
        }
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
  EventBus.emit('painelset:editorarea:close')
  nextTick(() => {
    visaoSelected.value = id
  })
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

const onChangePermission = () => {
  if (!authStore.isAuthenticated) {
    return false
  }
  return authStore.hasPermission('painelset.change_painel')
}

onMounted(() => {
  // Initial sync when component is mounted
  syncPainel()

  setTimeout(() => {
    if (visaoList.value.length === 0) {
      editmode.value = true
      activeTeleportId.value = painelsetPainel.value.id
    }
  }, 1000)
})

// 8. Functions
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
  }
  & > .painel-empty {
    flex: 1 1 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #888;
    font-size: 1.2em;
    text-align: center;
    padding: 2em;
  }
  & > .actions {
    line-height: 1;
    text-align: right;
    height: 0.5em;
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

</style>
