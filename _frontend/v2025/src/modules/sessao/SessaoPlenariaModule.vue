<template>
  <div class="sessaoplenaria-module">
    <router-view />
    <PopoverPalavra />
    <div
      id="modalCmj"
      ref="modalCmj"
    />
  </div>
</template>

<script setup>
import PopoverPalavra from '~@/modules/painelset/popovers/PopoverPalavra.vue'
import { useSyncStore } from '~@/stores/SyncStore'
import { ref, onMounted } from 'vue'

const syncStore = useSyncStore()

const modalCmj = ref(null)

const fetchInitialData = async () => {
  syncStore.registerModels('materia', [
    'tramitacao', // não há fetch direto, mas pode chegar atualizações via websocket
    'documentoacessorio'
  ])
  syncStore.registerModels('norma', [
    'normajuridica', // não há fetch direto, mas pode chegar atualizações via websocket
    'legislacaocitada'
  ])

  syncStore.syncModels([
    // { app: 'parlamentares', models: ['legislatura', 'sessaolegislativa'] },
    // { app: 'base', models: ['autor'] },
    // { app: 'parlamentares', models: ['parlamentar'], params: { ativo: 'True' } },
    { app: 'materia', models: ['statustramitacao'] },
    { app: 'sessao', models: ['tiposessaoplenaria'] }
  ], { page_size: 100 })

}

onMounted(() => {
  fetchInitialData()
})

</script>

<style lang="scss">
.sessaoplenaria-module {
  // line-height: 1.2;
}
</style>
