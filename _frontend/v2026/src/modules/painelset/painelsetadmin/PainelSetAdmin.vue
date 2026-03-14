<template>
  <div class="painelset-admin">
    <div class="container-grid">
      <div class="row header">
        <div class="col">
          <div class="titulo-evento">
            {{ evento ? evento.name : 'Carregando evento...' }}
            <small>
              {{ datahora_prevista_real[0] }} - {{ datahora_prevista_real[1] }} {{ datahora_prevista_real[2] }}
            </small>
          </div>
        </div>
        <div class="col-auto">
          <cronometro-base
            v-if="cronometro"
            :cronometro_id="cronometro.id"
            css_class_controls="hover"
            css_class="cronometro-global"
            :controls="['start', 'pause', 'resume', 'toggleDisplay'] "
            @cronometro_start="startEvento()"
            @cronometro_pause="pauseEvento()"
            @cronometro_resume="resumeEvento()"
          />
        </div>
      </div>
      <div class="row">
        <div class="col-5 container-individuos">
          <individuo-list
            v-if="evento"
            :evento="evento"
            ref="individuoListRef"
            :pause_parent_on_start="cronometro && cronometro.pause_parent_on_start"
          />
        </div>
        <div class="col-7 container-controls">
          <palavra-em-uso
            v-if="evento"
            :evento="evento"
          />
          <visoes-control
            v-if="evento"
            :evento="evento"
          />
        </div>
      </div>
    </div>
    <div
      class="disabled"
      v-if="cronometro && cronometro.state !== 'running'"
    >
      <div class="overlay-paused">
        <div class="text-paused">
          <div v-if="cronometro && cronometro.state === 'paused'">
            EVENTO EM SUSPENSÃO
          </div>
          <div v-else-if="cronometro && cronometro.state === 'stopped'">
            EVENTO NÃO INICIADO
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'
import CronometroBase from './CronometroBase.vue'
import IndividuoList from './IndividuoList.vue'
import PalavraEmUso from './PalavraEmUso.vue'
import VisoesControl from './VisoesControl.vue'

const route = useRoute()
const router = useRouter()
const syncStore = useSyncStore()
const authStore = useAuthStore()
const messageStore = useMessageStore()

const evento_id = Number(route.params.id)
const finished = ref(false)
const individuoListRef = ref(null)

const evento = computed(() => {
  return syncStore.data_cache['painelset_evento'] ? syncStore.data_cache['painelset_evento'][evento_id] : null
})

const cronometro = computed(() => {
  return evento.value && evento.value.cronometro
    ? syncStore.data_cache['painelset_cronometro']
      ? syncStore.data_cache['painelset_cronometro'][evento.value.cronometro]
      : null
    : null
})

const datahora_prevista_real = computed(() => {
  if (evento.value && !evento.value.start_real) {
    const dt = new Date(evento.value.start_previsto)
    return ['Início previsto', dt.toLocaleDateString(), dt.toLocaleTimeString()]
  } else if (evento.value && evento.value.start_real) {
    const dt = new Date(evento.value.start_real)
    return ['Iniciado em', dt.toLocaleDateString(), dt.toLocaleTimeString()]
  }
  return ['Data e hora não definidas', '', '']
})

watch(() => evento.value, (newVal) => {
  if (!finished.value && newVal && newVal.end_real) {
    finished.value = true
    messageStore.addMessage({ type: 'danger', text: 'Evento já finalizado. Você pode copiá-lo para gerar um novo evento.', timeout: 10000 })
    router.push({ name: 'painelsetadmin_evento_list_link' })
  }
  if (newVal && newVal.cronometro) {
    return syncStore.fetchSync({
      app: 'painelset',
      model: 'cronometro',
      id: newVal.cronometro
    })
  }
}, { immediate: true })

onMounted(() => {
  setTimeout(() => {
    if (authStore.permissions.includes('painelset.change_evento')) {
      syncStore.fetchSync({
        app: 'painelset',
        model: 'evento',
        id: evento_id
      })
    } else {
      router.push({ name: 'online_index_link' })
      messageStore.addMessage({ type: 'danger', text: 'Você não tem permissão para acessar esta página. aqui 2', timeout: 5000 })
    }
  }, 1000)
})

const resumeEvento = () => {
  individuoListRef.value.status_microfone = 0
  individuoListRef.value.toggleAllMicrofones()
}

const startEvento = () => {
  Resources.Utils.patchModel({
    app: 'painelset',
    model: 'evento',
    id: evento.value.id,
    action: 'start'
  })
    .then(response => {
      console.debug('start response', response)
    })
    .catch(error => {
      console.error('start error', error)
    })
}

const pauseEvento = () => {
  individuoListRef.value.status_microfone = 1
  individuoListRef.value.toggleAllMicrofones(false)
}
</script>

<style lang="scss">
.painelset-admin {
  $px: 0px;
  line-height: 1;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #222;
  .container-grid {
    padding: 0 $px;
    height: 100%;
  }
  .row {
    position: relative;
    align-items: stretch;
    margin-left: -$px;
    margin-right: -$px;
    padding-top: $px;
    &:first-child {
      height: 3.4em;
    }
    &:last-child {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      top: 3.4em;
    }
    div[class^=col] {
      position: static;
      padding-left: $px;
      padding-right: $px;
      &:not(:first-child) {
        padding-left: $px / 2;
      }
      &:not(:last-child) {
        padding-right: $px / 2;
      }
    }
    &.header {
      .col-auto {
        display: flex;
        align-items: stretch;
      }
    }
  }
  .titulo-evento {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    flex-direction: column;
    height: 100%;
    // border-radius: 8px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    background-color: #444;
    color: #eee;
    font-size: 1.1em;
    font-weight: bold;
    line-height: 1;
    padding: 5px 10px;
  }
  .evento-datahora {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    padding: 5px 10px;
    // border-radius: 8px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    background-color: #444;
    color: #eee;
    font-size: 0.8em;
    font-weight: bold;
    line-height: 1;
    .evento-data {
      font-size: 1.2em;
    }
    .evento-hora {
      font-size: 1.1em;
    }
  }

  .disabled {
    // pointer-events: none;
  }
  .overlay-paused {
    position: absolute;
    top: 5.42em;
    left: 41.6667%;
    right: 0;
    bottom: 3.5em;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    .text-paused {
      color: #fff;
      font-size: 4em;
      font-weight: bold;
      text-shadow: 0 0 50px rgba(120, 6, 6, 0.7);
      text-align: center;
    }
  }
}
@media screen and (max-width: 991.98px) {
  .painelset-admin {
    .row {
      div[class^=col] {
        position: relative;
      }
    }
    .titulo-evento {
      font-size: 1em;
      padding: 5px 5px;
    }
    .cronometro-global {
      display: flex;
      height: 3.4em;
      .croncard {
        padding: 0;
      }
    }
    .overlay-paused {
      .text-paused {
        font-size: 3em;
      }
    }
  }
}
</style>
