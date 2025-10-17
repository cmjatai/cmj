<template>
  <div class="painelset-painel">
    <router-view />
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useRoute, useRouter } from 'vue-router'
import { watch, ref } from 'vue'

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

let painelId = ref(Number(route.params.painel_id))
let painelVisaoId = ref(Number(route.params.painelvisao_id))

const syncComponent = async () => {
  if (painelId.value) {
    syncStore
      .fetchSync({
        app: 'painelset',
        model: 'painel',
        id: painelId.value
      })
      .then(() => {
        if (!painelVisaoId.value) {
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'painelvisao',
              params: {
                painel: painelId.value,
                active: true
              }
            })
            .then((response) => {
              if (response && response.data.results.length > 0) {
                const firstPainelVisao = response.data.results[0]
                painelVisaoId.value = firstPainelVisao.id
                router.push({ name: 'painelset_painel_visao_view', params: { painelvisao_id: firstPainelVisao.id } })
              }
            })
        }
      })
      .catch((error) => {
        // router push to 404
        console.error('Error fetching painel:', error)
        router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
      })
  } else {
    syncStore
      .fetchSync({
        app: 'painelset',
        model: 'evento',
        params: {
          end_real__isnull: true,
          start_real__isnull: false
        }
      })
      .then((response) => {
        if (response && response.data.results.length > 0) {
          const evento = response.data.results[0]
          syncStore
            .fetchSync({
              app: 'painelset',
              model: 'painel',
              params: {
                evento: evento.id
              }
            })
            .then((painelResponse) => {
              if (painelResponse && painelResponse.data.results.length > 0) {
                const firstPainel = painelResponse.data.results[0]
                painelId.value = firstPainel.id
                router.push({ name: 'painelset_painel_view', params: { painel_id: firstPainel.id } })
              } else {
                router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
              }
            })
        } else {
          router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
        }
      })
      .catch((error) => {
        // router push to 404
        console.error('Error fetching evento:', error)
        router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
      })
  }
}

syncComponent()

watch(
  () => route.params.painel_id, (nv) => {
    painelId.value = nv
    syncComponent()
  },
  () => route.params.painelvisao_id, (nv) => {
    painelVisaoId.value = nv
    syncComponent()
  },
  { immediate: true }
)
</script>
<style scoped>
</style>
