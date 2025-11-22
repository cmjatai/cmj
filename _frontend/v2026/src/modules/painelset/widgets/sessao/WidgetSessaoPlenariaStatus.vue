<template>
  <div
    class="widget-sessao-plenaria-status"
  >
    <div
      class="title"
      v-if="props.showFields.includes('__str__')"
      v-html="strSplitted"
    />
    <div class="container-fluid" v-if="props.showFields.length > 1 && sessaoPlenaria">
      <div class="row">
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('data_inicio')"
        >
          <div class="inner-col">
            <div class="label">Data de Início:</div>
            <div class="data-inicio">
              {{ reverseDateString(sessaoPlenaria?.data_inicio) }}
            </div>
          </div>
        </div>
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('data_fim')"
        >
          <div class="inner-col">
            <div class="label">Data de Término:</div>
            <div class="data-fim">
              {{ reverseDateString(sessaoPlenaria?.data_fim) || 'Em andamento' }}
            </div>
          </div>
        </div>
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('hora_inicio')"
        >
          <div class="inner-col">
            <div class="label">Hora de Início:</div>
            <div class="hora-inicio">
              {{ sessaoPlenaria?.hora_inicio }}
            </div>
          </div>
        </div>
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('hora_fim')"
        >
          <div class="inner-col">
            <div class="label">Hora de Término:</div>
            <div class="hora-fim">
              {{ sessaoPlenaria?.hora_fim || 'Em andamento' }}
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('iniciada')"
        >
          <div class="inner-col">
            <div class="label">Iniciada:</div>
            <div class="iniciada">
              {{ sessaoPlenaria?.iniciada ? 'Sim' : 'Não' }}
            </div>
          </div>
        </div>
        <div
          :class="`col-${props.cols}`"
          v-if="props.showFields.includes('finalizada')"
        >
          <div class="inner-col">
            <div class="label">Finalizada:</div>
            <div class="finalizada">
              {{ sessaoPlenaria?.finalizada ? 'Sim' : 'Não' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  },
  showFields: {
    type: Array,
    default: () => ['__str__']
  },
  cols: {
    type: Number,
    default: 6
  }
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const sessaoPlenaria = computed(() => {
  return syncStore.data_cache.sessao_sessaoplenaria
    ?.[painel.value?.sessao] || null
})

const strSplitted = computed(() => {
  if (!sessaoPlenaria.value || !sessaoPlenaria.value.__str__) {
    return []
  }
  const regex = /(\d{4})/g
  let str = sessaoPlenaria.value.__str__
  console.debug('str', str)
  const match = regex.exec(str)
  if (!match) {
    return str
  }
  str = `<span>${str.substring(0, match.index + 4)}</span><span>${str.substring(match.index + 5)}</span>`
  return str
})

const reverseDateString = (str) => {
  return str?.split('-').reverse().join('/')
}

</script>
<style lang="scss" scoped>
  .widget-sessao-plenaria-status {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    .title {
      display: flex;
      flex-direction: column;
    }
    .container-fluid {
      padding-top: 0.6em;
    }
    .inner-col {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5em;
      font-size: 0.9em;
    }
  }
</style>
