<template>
  <div class="individuo-list">
    <div :class="['individuo-base', 'manager',
      status_microfone ? '' : 'muted']">
      <div class="inner">
        <div class="controls">
          <button
          class="btn-action btn-fone"
          title="Ativar/Desativar Todos os Microfones"
          @click="toggleAllMicrofones()"
        >
          <FontAwesomeIcon :icon="status_microfone ? 'microphone' : 'microphone-slash'" size="2x" />
        </button>
        </div>
        <div class="inner-individuo py-2">{{ individuos.length }} CANAIS</div>
        <div class="inner-individuo">
          <div class="default-timer">
            <button class="btn btn-link">
              <FontAwesomeIcon icon="arrow-down" @click="default_timer > 60 ? default_timer -= 60 : default_timer = 60" />
            </button>
            Tempo Padrão: {{ (default_timer / 60).toFixed(0) }} min
            <button class="btn btn-link">
              <FontAwesomeIcon icon="arrow-up" @click="default_timer < 600 ? default_timer += 60 : default_timer = 600" />
            </button>
          </div>
        </div>
        <div class="inner-individuo">
          <input
            type="checkbox"
            id="pause_parent_on_aparte"
            v-model="pause_parent_on_aparte"
            title="Pausar o Cronômetro de quem está com a palavra quando alguém solicitar aparte"
          />
        </div>
      </div>
    </div>
    <div class="individuos">
      <individuo-base
      v-for="individuo in individuos"
      :key="`individuo-${individuo.id}-${individuo.order}`"
      :ref="`individuo-${individuo.id}`"
      :individuo_id="individuo.id"
      :default_timer="default_timer"
      />
    </div>
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'
import IndividuoBase from './IndividuoBase.vue'

const syncStore = useSyncStore()
const messageStore = useMessageStore()

const props = defineProps({
  evento: {
    type: Object,
    required: true
  },
  pause_parent_on_start: {
    type: Boolean,
    required: false,
    default: false
  }
})

const status_microfone = ref(false)
const pause_parent_on_aparte = ref(props.pause_parent_on_start)
const default_timer = ref(300)

const individuos = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return _.orderBy(
      _.filter(
        Object.values(syncStore.data_cache.painelset_individuo),
        { evento: props.evento.id }
      ),
      ['order'],
      ['asc']
    )
  }
  return []
})

const cronometros = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    const result = []
    for (const individuo of Object.values(syncStore.data_cache.painelset_individuo)) {
      if (individuo.evento === props.evento.id && individuo.cronometro) {
        result.push(syncStore.data_cache.painelset_cronometro[individuo.cronometro])
      }
    }
    return result
  }
  return []
})

watch(individuos, () => {
  status_microfone.value = individuos.value.every(
    individuo => individuo.status_microfone === true)
}, { deep: true })

watch(() => props.pause_parent_on_start, (newVal) => {
  pause_parent_on_aparte.value = newVal
})

watch(pause_parent_on_aparte, (newVal) => {
  if (cronometros.value && cronometros.value.length > 0) {
    if (cronometros.value[0] && cronometros.value[0].pause_parent_on_start === newVal) {
      return
    }
  }
  const query_params = {
    pause_parent_on_aparte: newVal ? 'on' : 'off'
  }
  Resources.Utils
    .patchModel({
      app: 'painelset',
      model: 'evento',
      id: props.evento.id,
      action: 'pause_parent_on_aparte',
      form: query_params
    })
    .then(response => {
      console.debug(props.evento, 'pause_parent_on_aparte', response)
    })
    .catch(error => {
      console.error(props.evento.id, 'pause_parent_on_aparte', error)
      messageStore.addMessage({ type: 'danger', text: 'Erro ao atualizar Configurar Pausa: ' + error.response.data, timeout: 5000 })
    })
})

onMounted(() => {
  console.debug('IndividuoList mounted', props.evento)
  syncStore.fetchSync({
    app: 'painelset',
    model: 'individuo',
    params: { evento: props.evento.id }
  })
})

const toggleAllMicrofones = (inclui_microfone_sempre_ativo = true) => {
  status_microfone.value = !status_microfone.value
  const query_params = {
    status_microfone: status_microfone.value ? 'on' : 'off',
    inclui_microfone_sempre_ativo: inclui_microfone_sempre_ativo ? 'on' : 'off'
  }
  Resources.Utils
    .patchModel({
      app: 'painelset',
      model: 'evento',
      id: props.evento.id,
      action: 'toggle_microfones',
      form: query_params
    })
    .then(response => {
      console.debug(props.evento, 'toggle_microfones', response)
    })
    .catch(error => {
      console.error(props.evento.id, 'toggle_microfones', error)
      messageStore.addMessage({ type: 'danger', text: 'Erro ao atualizar Microfones: ' + error.response.data, timeout: 5000 })
    })
}

defineExpose({ status_microfone, toggleAllMicrofones })
</script>
<style lang="scss">
.individuo-list {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
  width: 37%;
  justify-content: stretch;
  position:absolute;
  top:0;
  left:0;
  bottom:0;
  overflow: hidden;
  .individuos {
    position: absolute;
    display: flex;
    flex-direction: row;
    //justify-content: space-between;
    top: 2.1em;
    bottom: 0;
    width: 100%;
    flex-wrap: wrap;
    .individuo-base {
      flex: 0 0 100%;
    }
  }
  .individuo-base.manager {
    flex: 0 0 3em;
    border-bottom: 1px solid #fff;
    font-size: 0.7em;
    .inner-individuo, .controls {
      border-right: 0;
      font-weight: bold;
      opacity: 1 !important;
      text-align: center;
    }
    .inner-individuo {
      border-left: 1px solid white;
      cursor: default;
      justify-content: center;
      font-size: 1.2em;
      .default-timer {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        gap: 0.5em;
        .btn {
          padding: 0 0.25em;
          color: #0004;
          text-decoration: none;
          &:hover {
            color: #000;
          }
        }
      }
    }
  }
}
@media screen and (max-width: 991.98px) {
  .individuo-list {
    width: 100%;
    overflow: visible;
    background-color: #222;
    .individuo-base {
      &.manager {
        position: static;
        height: 3em;
        z-index: 1;
        .inner {
          position: absolute;
          overflow: visible;
          top: 0;
          left: 0;
          right: 0;
          height: 3em;
          width: calc(100vw - 48px);
          z-index: 0;
        }
      }
    }
  }
}
</style>
