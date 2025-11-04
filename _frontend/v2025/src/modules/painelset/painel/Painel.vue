<template>
  <div
    :id="`id-painelset-painel-${painelId}`"
    ref="painelsetPainel"
    :key="`painelset-painel-${painelId}`"
    class="painelset-painel"
    :style="{...painel?.styles.component || {}, fontSize: `${zoomFont}em`}"
    @mousemove="movingSobrePainel($event)"
  >
    <div
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
        :editmode-visao="editmodeVisao"
      />
    </div>
    <div class="painel-empty" v-else>
      <p>Não há visões de painel configuradas para este painel.</p>
      <p>Utilize o botao de adição na tela de configurações para adicionar a primeira visão do painel.</p>
    </div>
    <div class="actions">
      <div
        class="btn-group btn-group-sm"
        role="group"
        aria-label="Zoom da fonte"
        :title="`Zoom aplicado aos elementos textuais: ${(zoomFont*100).toFixed(0)}%`"
      >
        <button class="btn btn-link">{{ (zoomFont * 100).toFixed(0) }}%</button>
        <button class="btn btn-link btn-zoom-out" @click.stop.prevent="zoomFontChange(-0.1)">
          <FontAwesomeIcon
            :icon="'fa-solid fa-angles-down'"
          />
        </button>
        <button class="btn btn-link btn-zoom-out" @click.stop.prevent="zoomFontChange(-0.01)">
          <FontAwesomeIcon
            :icon="'fa-solid fa-angle-down'"
          />
        </button>
        <button class="btn btn-link btn-zoom-in" @click.stop.prevent="zoomFontChange(0.01)">
          <FontAwesomeIcon
            :icon="'fa-solid fa-angle-up'"
          />
        </button>
        <button class="btn btn-link btn-zoom-in" @click.stop.prevent="zoomFontChange(0.1)">
          <FontAwesomeIcon
            :icon="'fa-solid fa-angles-up'"
          />
        </button>
        <div
          v-if="onChangePermission()"
          class="btn-group"
          role="group"
          aria-label="Visões do Painel"
        >
          <button
            class="btn btn-link btn-editmode"
            @click.stop.prevent="clickEditMode($event)"
            :title="editmode ? 'Sair do modo de edição' : 'Entrar no modo de edição'"
            :class="{ active: editmode }"
          >
            <FontAwesomeIcon
              :icon="'fa-solid fa-pen-to-square'"
              size="1x"
            />
          </button>
        </div>
      </div>
      <div class="toolbar">
        <div
          class="btn-group"
          role="group"
          aria-label="Visões do Painel"
        >
          <div
            v-if="onChangePermission()"
            class="btn-group"
            role="group"
            aria-label="Visões do Painel"
          >
            <button
              class="btn btn-link btn-editmode"
              @click.stop.prevent="clickEditModeVisao($event)"
              :title="editmodeVisao ? 'Sair do modo de edição' : 'Entrar no modo de edição'"
              :class="{ active: editmodeVisao }"
            >
              <FontAwesomeIcon
                :icon="'fa-solid fa-pen-to-square'"
                size="1x"
              />
            </button>
          </div>
          <button
            v-for="(pv, index) in visaoList"
            :key="`${pv.id}_${index}`"
            :class="{ active: pv.id === visaoSelected }"
            class="btn btn-secondary"
            @mousedown.stop.prevent="false"
            @click.stop.prevent="trocarVisao(pv.id)"
          >
            {{ pv.position }}
          </button>
        </div>
      </div>
    </div>

    <Teleport
      v-if="editmode"
      to="#painelset-editorarea"
      :disabled="!editmode"
    >
      <PainelEditor
        :painel-id="painelId"
        :painel-selected="painelId"
      />
    </Teleport>
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
import PainelEditor from './editors/PainelEditor.vue'

// 2. Composables
const EventBus = inject('EventBus')
const syncStore = useSyncStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()


// 3. Props & Emits
const props = defineProps({
  painelId: {
    type: String,
    default: '0'
  },
  zoomFontProp: {
    type: Number,
    default: 1
  }
})

// 4. State & Refs
const editmode = ref(false)
const editmodeVisao = ref(false)

const painelsetPainel = ref(null)
const initMovingSobrePainel = ref(false)
const idTimerMovingSobrePainel = ref(null)
const visaoSelected = ref(null)
const zoomFont = ref(props.zoomFontProp)

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

// 6. Watchers
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
  () => painel.value?.sessao,
  (newSessao) => {
    if (newSessao) {
      syncStore
        .fetchSync({
          app: 'sessao',
          model: 'sessaoplenaria',
          id: newSessao
        })
    }
  },
  {
    immediate: true
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
      if (activeTeleportId.value !== null) {
        if (!newVisaoList.find((pv) => pv.id === visaoSelected.value?.id)) {
          visaoSelected.value = newVisaoList[0].id
        }
        return
      }
      const visaoAtivaLocal = newVisaoList.find(
        (pv) => pv.active === true
      )
      if (visaoAtivaLocal) {
        visaoSelected.value = visaoAtivaLocal.id
      } else {
        visaoSelected.value = newVisaoList[0].id
      }
    } else {
      visaoSelected.value = null
    }
  },
  {
    immediate: true,
    deep: true
   }
)

// 7. Events & Lifecycle Hooks
const zoomFontChange = (delta) => {
  if (delta > 0) {
    zoomFont.value = Math.min(3, zoomFont.value + delta)
  } else {
    zoomFont.value = Math.max(0.1, zoomFont.value + delta)
  }
}

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
      .then((data_cache_painel) => {
        if (data_cache_painel[painelId.value].sessao) {
          syncStore
            .fetchSync({
              app: 'sessao',
              model: 'sessaoplenaria',
              id: data_cache_painel[painelId.value].sessao
            })
        }
        if (data_cache_painel[painelId.value].evento) {
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'evento',
              id: data_cache_painel[painelId.value].evento
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
      .then((data_cache_evento) => {
        const listaEvento = _.orderBy(
          Object.values(data_cache_evento || {}), ['start_real'], ['asc']
        ).filter(
          (ev) => ev.end_real === null
        )
        if (listaEvento && listaEvento.length > 0) {
          const evento = listaEvento[0]
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'painel',
              params: {
                evento: evento.id,
                principal: true
              }
            })
            .then((data_cache_painel) => {
              const listaPainel = _.orderBy(
                Object.values(data_cache_painel || {}), ['position'], ['asc']
              )
              if (listaPainel && listaPainel.length > 0) {
                const firstPainel = listaPainel[0]
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
  nextTick(() => {
    visaoSelected.value = id
  })
}

const visaoAtiva = () => {
  if (activeTeleportId.value !== null) {
    return
  }
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
      clickEditMode()
    }
  }, 1500)
})

EventBus.on('painelset:editorarea:close', () => {
  editmode.value = false
  editmodeVisao.value = false
  activeTeleportId.value = null
})

const clickEditMode = () => {
  if (!onChangePermission()) {
    return
  }
  EventBus.emit('painelset:editorarea:close')
  editmode.value = true
  editmodeVisao.value = false
  activeTeleportId.value = painelsetPainel.value.id
}

const clickEditModeVisao = () => {
  if (!onChangePermission()) {
    return
  }
  EventBus.emit('painelset:editorarea:close')
  editmode.value = false
  editmodeVisao.value = true
}

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
    .then((data_cache_visao) => {
      const listaVisao = _.orderBy(
        Object.values(data_cache_visao || {}), ['position'], ['asc']
      ).find(
        (pv) => pv.active === true
      )
      if (listaVisao && listaVisao.length > 0) {
        const visaoAtiva = listaVisao
        if (visaoAtiva) {
          visaoSelected.value = visaoAtiva.id
        } else {
          visaoSelected.value = listaVisao[0].id
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
    height: 4px;
    width: 100%;
    display: flex;
    justify-content: space-between;
    overflow: hidden;
    .btn {
      font-size: 16px;
      padding: 0.6em;
      line-height: 1;
      border-radius: 0;
      opacity: 1;
      text-decoration: none;
    }
    .btn-zoom-in, .btn-zoom-out {
      // transform: rotate(-90deg);
    }
    &:hover {
      height: auto;
      .btn {
        height: auto;
        opacity: 1;
      }
    }
  }
}

</style>
