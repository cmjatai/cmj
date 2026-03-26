<template>
  <div class="painelset-evento-list">
    <div class="header">
      <h1>Eventos e Painéis Eletrônicos</h1>
    </div>
    <div class="container">
      <painel-set-evento-list-item
        v-for="evento in eventos"
        :key="`evento-${evento.id}`"
        :evento="evento"
      />
    </div>
    <router-view></router-view>
  </div>
</template>

<script setup>
import { computed, onMounted, defineAsyncComponent } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const PainelSetEventoListItem = defineAsyncComponent(() => import('./PainelSetEventoListItem.vue'))

const eventos = computed(() => {
  if (syncStore.data_cache?.painelset_evento) {
    return _.orderBy(Object.values(syncStore.data_cache.painelset_evento), ['end_real', 'start_real', 'start_previsto'], ['desc', 'desc', 'desc'])
  }
  return []
})

onMounted(() => {
  syncStore.fetchSync({
    app: 'painelset',
    model: 'evento',
    params: { o: '-start_real,-start_previsto' }
  })
  syncStore.registerModels('painelset', ['evento'])
  syncStore.registerModels('sessao', ['sessaoplenaria'])

  syncStore.fetchSync({
    app: 'sessao',
    model: 'sessaoplenaria',
    params: {
      o: '-data_inicio'
    },
    only_first_page: true
  })
})
</script>

<style lang="scss">
.painelset-evento-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: auto;
  user-select: none;

  .header {
    background: white;
    padding: 10px 20px;
    h1 {
      margin: 0;
      font-weight: 600;
    }
  }

  .container {
    margin-top: 20px;
  }

  .row {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
  }

  .col-auto {
    display: flex;
    align-items: center;
    justify-content: center;
    .btn {
      font-size: 1em;
    }

  }
}
</style>
