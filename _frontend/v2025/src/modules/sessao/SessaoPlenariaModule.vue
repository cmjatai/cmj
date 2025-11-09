<template>
  <div class="sessaoplenaria-module">
    <router-view></router-view>
  </div>
</template>

<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { onMounted } from 'vue'

const syncStore = useSyncStore()

const fetchInitialData = async () => {

  syncStore.syncModels([
    // { app: 'parlamentares', models: ['legislatura', 'sessaolegislativa'] },
    { app: 'parlamentares', models: ['parlamentar'], params: { ativo: 'True' } },
    { app: 'base', models: ['autor'] },
    { app: 'materia', models: ['tipomaterialegislativa'] },
    { app: 'sessao', models: ['tiposessaoplenaria'] }
  ], { page_size: 100 })

}

onMounted(() => {
  fetchInitialData()
})

</script>

<style lang="scss">
</style>
