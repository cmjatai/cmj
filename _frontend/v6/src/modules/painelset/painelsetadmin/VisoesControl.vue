<template>
  <div class="painelset-visoes-control">
    <div class="youtube_id">
      <input type="text" v-model="youtube_id" @change="patchYoutubeId"/>
    </div>
    <div class="inner" v-if="painel">
      <div class="checkbox-auto-select-visoes">
        <input
          type="checkbox"
          id="autoSelectVisoes"
          v-model="painel.auto_select_visoes"
          @change="patchAutoSelectVisoes"
        >
      </div>
      <div class="inner-visoes">
        <div class="title-visao-ativa">
          <div v-if="visoes.length > 0">
            <span v-for="visao in visoes" :key="`visao-ativa-${visao.id}`">
              <span v-if="visao.active"><FontAwesomeIcon icon="check-circle" />
                {{ visao.name }}
              </span>
            </span>
          </div>
        </div>
        <div class="lista-visoes btn-group">
          <a
            v-for="visao in visoes" :key="`visao-control-${visao.id}`"
            :class="['btn btn-secondary', visao.active ? 'active' : '', visao.config.only_manual_activation ? 'btn-warning' : '']"
            :title="visao.name"
            @click="manualActiveVisao(visao.id)"
            >
            {{ visao.position }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'

const route = useRoute()
const router = useRouter()
const syncStore = useSyncStore()
const authStore = useAuthStore()
const messageStore = useMessageStore()

const props = defineProps({
  evento: {
    type: Object,
    required: true
  }
})

const evento_id = Number(route.params.id)
const youtube_id = ref('')
const finished = ref(false)

const painel = computed(() => {
  if (props.evento && syncStore.data_cache?.painelset_painel) {
    return Object.values(syncStore.data_cache?.painelset_painel).find(p => p.evento === props.evento.id) || null
  }
  return null
})

const visoes = computed(() => {
  if (painel.value && syncStore.data_cache?.painelset_visaodepainel) {
    return _.orderBy(
      _.filter(
        Object.values(syncStore.data_cache?.painelset_visaodepainel),
        { painel: painel.value.id }
      ),
      ['position'],
      ['asc']
    )
  }
  return []
})

watch(() => props.evento, (newVal) => {
  if (!finished.value && newVal && newVal.end_real) {
    finished.value = true
    messageStore.addMessage({ type: 'danger', text: 'Evento já finalizado. Você pode copiá-lo para gerar um novo evento.', timeout: 10000 })
    router.push({ name: 'painelsetadmin_evento_list_link' })
  }
  if (newVal) {
    youtube_id.value = newVal.youtube_id || ''
    syncStore.fetchSync({
      app: 'painelset',
      model: 'painel',
      params: {
        evento: newVal.id,
        principal: true
      }
    })
      .then(() => {
        syncStore.fetchSync({
          app: 'painelset',
          model: 'visaodepainel',
          params: { painel: painel.value.id }
        })
      })
  }
}, { immediate: true })

onMounted(() => {
  nextTick(() => {
    if (authStore.permissions.includes('painelset.change_evento')) {
      syncStore.registerModels('painelset', ['evento', 'painel', 'visaodepainel'])
      syncStore.fetchSync({
        app: 'painelset',
        model: 'evento',
        id: evento_id
      })
    } else {
      router.push({ name: 'online_index_link' })
      messageStore.addMessage({ type: 'danger', text: 'Você não tem permissão para acessar esta página. aqui1', timeout: 5000 })
    }
  })
})

const manualActiveVisao = (visao_id) => {
  Resources.Utils
    .patchModel({
      app: 'painelset',
      model: 'visaodepainel',
      id: visao_id,
      action: 'activate'
    })
    .then(response => {
    })
    .catch(error => {
      console.error(props.evento.id, 'active', error)
      messageStore.addMessage({ type: 'danger', text: 'Erro ao atualizar Visão Ativa: ' + error.response.data, timeout: 5000 })
    })
}

const patchYoutubeId = () => {
  Resources.Utils.patchModel({
    app: 'painelset',
    model: 'evento',
    id: props.evento.id,
    form: { youtube_id: youtube_id.value }
  })
}

const patchAutoSelectVisoes = () => {
  Resources.Utils.patchModel({
    app: 'painelset',
    model: 'painel',
    id: painel.value.id,
    form: { auto_select_visoes: painel.value.auto_select_visoes }
  })
}
</script>

<style lang="scss">
.painelset-visoes-control {
  position: absolute;
  left: 37%;
  right: 0;
  bottom: 0em;
  background-color: #222;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  color: white;

  .inner {
    display: flex;
    flex-direction: row;
    align-items: center;
  }

  .checkbox-auto-select-visoes {
    zoom: 2;
    input {
      margin: 0 0.5em;
    }
  }
  .youtube_id {
    width: 100%;
    padding: 0.5em 0.5em 0;
    input {
      width: 100%;
    }
  }
  .inner-visoes {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .title-visao-ativa {
    min-height: 1.5em;
    text-align: center;
    margin-top: 1em;
  }

  .lista-visoes {
    display: flex;
    flex-direction: row;
    margin: 0.5em;
    .btn {
      padding-left: 2em;
      padding-right: 2em;
      &:not(:last-child) {
        margin-right: 2px;
      }
    }
  }
}
@media (max-width: 768px) {
  .painelset-visoes-control {
    left: 0;
    right: 0;
    bottom: 0em;
    .checkbox-auto-select-visoes {
      zoom: 1.5;
      input {
        margin: 0 0.3em;
      }
    }
    .lista-visoes {
      .btn {
        padding-left: 0.6em;
        padding-right: 0.6em;
      }
    }
  }
}
</style>
