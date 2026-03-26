<template>
  <div
    :class="[
      'individuo-base',
      individuo && individuo.status_microfone ? '' : 'muted',
      individuo && individuo.parlamentar ? 'parlamentar' : '',
      individuo && individuo.com_a_palavra ? 'com-a-palavra' : (individuo && individuo.microfone_sempre_ativo ? 'always-on' : 'active'),
      individuo && individuo.aparteado ? 'aparteante' : ''
    ]"
  >
    <div class="inner">
      <div
        :class="['inner-individuo', fotografiaUrl ? '' : 'no-photo']"
        @click="clickIndividuo($event)"
        @dblclick="dblclickIndividuo($event)"
      >
        <div class="avatar">
          <img
            v-if="fotografiaUrl"
            :src="fotografiaUrl"
            alt="Foto do individuo"
          >
          <FontAwesomeIcon
            v-else
            icon="user"
          />
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
          <small>{{ individuo ? `(${individuo.canal})` : '' }}</small>
        </div>
      </div>
      <div class="controls">
        <button
          v-if="individuo"
          class="btn-action btn-fone"
          :title="individuo && !individuo.status_microfone ? 'Ativar microfone' : 'Desativar microfone'"
          @click="toggleMicrofone()"
        >
          <FontAwesomeIcon
            :icon="individuo && individuo.status_microfone ? 'microphone' : 'microphone-slash'"
            size="2x"
          />
        </button>
        <button
          class="btn-action btn-aparte"
          @click.prevent="clickIndividuo($event)"
          title="Solicitar aparte"
        >
          <FontAwesomeIcon icon="hand-rock" />
        </button>
        <button
          class="btn-action btn-palavra"
          @click.stop="dblclickIndividuo($event)"
          title="Solicitar a palavra"
        >
          <FontAwesomeIcon icon="hand-paper" />
        </button>
        <button
          v-if="false && individuo"
          class="btn-action btn-manage"
        >
          <FontAwesomeIcon icon="cog" />
        </button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, inject } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'

const syncStore = useSyncStore()
const messageStore = useMessageStore()
const EventBus = inject('EventBus')

const props = defineProps({
  individuo_id: {
    type: Number,
    required: true
  },
  default_timer: {
    type: Number,
    required: false,
    default: 300
  },
  default_timer_aparteante: {
    type: Number,
    required: false,
    default: 60
  }
})

const click_timeout = ref(null)

const individuoComPalavra = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return Object.values(syncStore.data_cache.painelset_individuo).find(i => i.com_a_palavra && i.evento === individuo.value.evento) || null
  }
  return null
})

const individuo = computed(() => {
  if (syncStore.data_cache?.painelset_individuo && props.individuo_id) {
    return syncStore.data_cache.painelset_individuo[props.individuo_id] || null
  }
  return null
})

const fotografiaUrl = computed(() => {
  if (individuo.value?.fotografia) {
    return '/api/painelset/individuo/' + individuo.value.id + '/fotografia.c96.png'
  } else if (individuo.value?.parlamentar) {
    return '/api/parlamentares/parlamentar/' + individuo.value.parlamentar + '/fotografia.c96.png'
  }
  return ''
})

const sendUpdate = (action, query_params) => {
  return Resources.Utils
    .patchModel({
      app: 'painelset',
      model: 'individuo',
      id: props.individuo_id,
      action: action,
      form: query_params
    })
    .then(response => {
      console.debug(props.individuo_id, action, response)
    })
    .catch(error => {
      console.error(props.individuo_id, action, error)
      messageStore.addMessage({ type: 'danger', text: 'Erro ao atualizar indivíduo: ' + error.response.data, timeout: 5000 })
    })
}

const toggleMicrofone = () => {
  sendUpdate(
    'toggle_microfone',
    {
      status_microfone: !individuo.value?.status_microfone ? 'on' : 'off',
      default_timer: props.default_timer,
      com_a_palavra: individuo.value?.com_a_palavra ? 1 : 0
    }
  )
}

const clickIndividuo = (event) => {
  clearTimeout(click_timeout.value)
  click_timeout.value = setTimeout(() => {
    if (individuo.value?.com_a_palavra || !individuoComPalavra.value) {
      if (individuo.value === individuoComPalavra.value) {
        messageStore.addMessage({ type: 'danger', text: 'A palavra já está sendo utilizada por este indivíduo.', timeout: 7000 })
        return
      }
      messageStore.addMessage({ type: 'danger', text: 'A palavra não está sendo utilizada. Não é possível fazer aparte.', timeout: 7000 })
      return
    }
    sendUpdate(
      'toggle_aparteante',
      {
        aparteante_status: !individuo.value.aparteado ? 1 : 0,
        default_timer: props.default_timer_aparteante || 60
      }
    )
  }, 600)
}

const dblclickIndividuo = (event) => {
  clearTimeout(click_timeout.value)
  sendUpdate(
    'toggle_microfone',
    {
      status_microfone: individuo.value?.status_microfone || !individuo.value?.com_a_palavra ? 'on' : 'off',
      default_timer: props.default_timer,
      com_a_palavra: !individuo.value?.com_a_palavra ? 1 : 0
    }
  )
}

const onToggleMicrofone = (individuo_id) => {
  if (individuo_id === props.individuo_id) {
    toggleMicrofone()
  }
}

onMounted(() => {
  console.debug('Individuo Base mounted', props.individuo_id)
  EventBus.on('toggle-microfone-individuo', onToggleMicrofone)
})

onBeforeUnmount(() => {
  EventBus.off('toggle-microfone-individuo', onToggleMicrofone)
})
</script>
<style lang="scss">
.individuo-base {
  display: flex;
  align-self: stretch;
  justify-content: stretch;
  border-bottom: 1px solid white;
  position: relative;
  &:last-child {
  border-bottom: 0px;
  }
  .inner {
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    flex-direction: row-reverse;
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: absolute;
  }
  .inner-individuo, .controls {
    display: flex;
    background-color: #ddffdd;
    align-items: stretch;
    flex: 1 1 auto;
    padding: 0;
  }
  &:not(.parlamentar):not(.manager):not(.muted) {
    .inner-individuo {
      background-color: #eee;
    }
  }
  .avatar {
    border-radius: 0;
    img {
      border-radius: 0;
      height: 100%;
    }
    i {
      margin: 0 0.5em 0 1em;
      font-size: 1.5em;
    }
  }
  .inner-individuo {
    cursor: pointer;
    align-items: center;
    gap: 10px;
    .name {
      flex: 1 1 100%;
      font-size: 1.3em;
      small {
        opacity: 0.5;
      }
    }
  }

  .controls {
    flex: 0 1 0;
    flex-direction: row-reverse;
    .btn-action {
      border: 0;
      border-right: 1px solid #fffa;
      width: 4.5em;
      background: transparent;
      font-size: 1.1em;
      color: #fff
    }
    .btn-palavra {
      background-color: #0364d3;
    }
    .btn-aparte {
      background-color: #d3a103;
    }
    .btn-manage {
      width: auto;
    }
  }
  .btn-fone-old, .btn-control-old {
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .fa-microphone {
    color: green;
    opacity: 0.6;
  }
  .fa-microphone-slash {
    opacity: 0.4;
  }
  &:hover {
    .inner-individuo, .controls {
      background: #bbffbb;
    }
  }
  &.muted {
    .inner-individuo, .controls {
      background: #ffdddd;
      opacity: 0.8;
    }
    &:hover {
      .inner-individuo, .controls {
        background: #ffcccc;
        opacity: 1;
      }
    }
  }
  &.com-a-palavra {
    border-left: 0;
    border-right: 0;
    .inner-individuo, .controls {
      background: linear-gradient(to right, #0364d3, #0253a8);
      opacity: 1 !important;
      font-weight: bold;
      color: white;
      .fa-microphone {
        color: #ff0;
        opacity: 1;
        font-size: 3em;
      }
      .btn-palavra {
        color: #000;
        background: #0005;
      }
    }
    .inner-individuo {
      font-size: 1.2em;
      border-color: transparent;
    }
  }
  &.aparteante {
    .inner-individuo, .controls {
      background: linear-gradient(to right, #d3a103, #a87f02);
      opacity: 1 !important;
      font-weight: bold;
      .fa-microphone {
        color: #ff0;
        opacity: 1;
        font-size: 3em;
      }
      .btn-aparte {
        color: #000;
        background: #0004;
      }
    }
    .inner-individuo {
      font-size: 1.2em;
      border-color: transparent;
    }
  }
  &.always-on:not(.muted):not(.com-a-palavra):not(.aparteante) {
    .inner-individuo, .controls {
      background: #7ee57e;
      opacity: 1 !important;
    }
  }
}
@media screen and (max-width: 991.98px) {
  .individuo-base {
    .inner-individuo {
      gap: 0;
    }
    .name {
      display: none;
    }
    .controls {
      .btn-action {
        width: 2.7em;
        font-size: 1em;
      }
      .fa-microphone, .fa-microphone-slash {
        font-size: 1.5em;
      }
    }
    .avatar {
      .fa-user {
        font-size: 1em;
        margin: 0;
        display: none;
      }
    }
    .no-photo {
      .name {
        display: block;
        font-size: 0.9em;
      }
    }
  }
}
</style>
