<template>
  <div class="painelset-painel">
    <router-view />
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useRoute, useRouter } from 'vue-router'

const syncStore = useSyncStore()
const route = useRoute()
const router = useRouter()

syncStore.registerModels('painelset', [
  'painel',
  'painelvisao',
  'evento'
])

syncStore.registerModels('sessao', [
  'sessaoplenaria'
])

syncStore.registerModels('materia', [
  'materialegislativa'
])

const painelId = route.params.painel_id
const painelVisaoId = route.params.painelvisao_id

if (painelId) {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'painel',
      id: painelId
    })
    .then(() => {
      if (!painelVisaoId) {
        syncStore
          .fetchSync({
            app: 'painelset',
            model: 'painelvisao',
            params: {
              painel: painelId,
              active: true
            }
          })
          .then((response) => {
            if (response && response.data.results.length > 0) {
              const firstPainelVisao = response.data.results[0]
              router.push({ name: 'painelset_painel_visao_view', params: { painelvisao_id: firstPainelVisao.id } })
            }
          })
      }
    })
    .catch((error) => {
      // router push to 404
      console.error('Error fetching painel:', error)
      router.push({ name: 'error_404', params: { pathMatch: 'error' } })
    })
}
</script>
<style scoped>
</style>
