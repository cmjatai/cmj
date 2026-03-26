<template>
  <div
    class="widget-status-evento-sessao"
  >
    <WidgetSessaoPlenariaStatus
      :painel-id="painelId"
      :widget-selected="widgetSelected"
      :cols="widgetContainer?.config.displayCols || 12"
      :show-fields="[
        widgetContainer?.config.displayTitulo ? '__str__' : null,
        widgetContainer?.config.displayDataInicio ? 'data_inicio' : null,
        widgetContainer?.config.displayHoraInicio ? 'hora_inicio' : null,
        widgetContainer?.config.displayIniciada ? 'iniciada' : null
      ]"
    />

    <div
      v-if="widgetContainer?.config.displayCronometro"
      class="cronometro-evento-sessao"
    >
      <div v-if="cronometro?.state === 'paused'">Sessão Suspensa</div>
      <WidgetCronometroBase
        v-if="evento?.cronometro"
        :painel-id="painelId"
        :widget-selected="widgetSelected"
        :cronometro-id="evento?.cronometro"
        :display-initial="'elapsed'"
      />
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

import WidgetCronometroBase from './WidgetCronometroBase.vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  }
})
const widgetContainer = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const evento = computed(() => {
  return syncStore.data_cache.painelset_evento
    ?.[painel.value?.evento] || null
})

const cronometro = computed(() => {
  return syncStore.data_cache.painelset_cronometro
    ?.[evento.value?.cronometro] || null
})

</script>
<style lang="scss" scoped>
  .widget-status-evento-sessao {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    .cronometro-evento-sessao {
      color: yellow;
      margin-top: 0.5em;
      font-size: 2.7em;
      font-weight: bold;
      .widget-cronometro-base {
        font-size: 1.4em;
      }
    }
  }
</style>
