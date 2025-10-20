<template>
  <div
    class="widget-sessao-plenaria-titulo"
  >
    {{ sessaoPlenaria?.__str__ }}
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
  }
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const sessaoPlenaria = computed(() => {
  return syncStore.data_cache.sessao_sessaoplenaria
    ?.[painel.value?.sessao] || null
})

const syncSessaoPlenaria = async () => {
  if (painel.value?.sessao) {
    await syncStore.fetchSync({
      app: 'sessao',
      model: 'sessaoplenaria',
      id: painel.value.sessao
    })
  }
}

syncSessaoPlenaria()

</script>
<style lang="scss" scoped>
  .widget-sessao-plenaria-titulo {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
