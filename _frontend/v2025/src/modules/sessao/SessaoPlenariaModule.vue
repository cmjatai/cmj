<template>
  <div class="sessaoplenaria-module online-module">
    sessao plenaria module
    <router-view></router-view>
    <popover-palavra></popover-palavra>
  </div>
</template>

<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { onMounted } from 'vue'

const syncStore = useSyncStore()

const fetchInitialData = async () => {

  // Fetch Legislatura
  syncStore.fetchSync({
    app: 'parlamentares',
    model: 'legislatura',
    params: {
      page_size: 100
    }
  })
  syncStore.fetchSync({
    app: 'parlamentares',
    model: 'sessaolegislativa',
    params: {
      page_size: 100
    }
  })

  // Fetch Parlamentares Ativos
  syncStore.fetchSync({
    app: 'parlamentares',
    model: 'parlamentar',
    params: {
      page_size: 100,
      ativo: 'True'
    }
  })

  // Fetch Autores
  syncStore.fetchSync({
    app: 'base',
    model: 'autor',
    params: {
      page_size: 100
    }
  })

  syncStore.fetchSync({
    app: 'materia',
    model: 'tipomaterialegislativa',
    params: {
      page_size: 100
    }
  })

  syncStore.fetchSync({
    app: 'sessao',
    model: 'tiposessaoplenaria',
    params: {
      page_size: 100
    }
  })
}

onMounted(() => {
  fetchInitialData()
})

</script>

<style lang="scss">
</style>
