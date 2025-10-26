<template>
  <div
    class="widget-status-evento-sessao"
  >

    <WidgetSessaoPlenariaStatus
      :painel-id="painelId"
      :widget-selected="widgetSelected"
      :show-fields="[
        '__str__',
        'data_inicio',
        'hora_inicio',
        'data_fim',
        'hora_fim',
        'iniciada',
        'finalizada'
      ]"
    />

    <div class="cronometro-evento-sessao">
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
      font-size: 2em;
      font-weight: bold;
    }
  }
</style>
