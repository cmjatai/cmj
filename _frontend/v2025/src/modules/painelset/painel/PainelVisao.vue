<template>
  <div class="painelset-painelvisao">
    {{ visao }}
    <br><br>
    <button @click="trocarVisao(1)">Visao 1</button>&nbsp;
    <button @click="trocarVisao(2)">Visao 2</button>&nbsp;
    <button @click="visaoAtiva()">Visao Ativa</button>
    <br><br>
    <button @click="ativarVisao(1)">Ativar Visao 1</button>&nbsp;
    <button @click="ativarVisao(2)">Ativar Visao 2</button>
    <br><br>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import Resource from '~@/utils/resources'

const syncStore = useSyncStore()
const route = useRoute()
const router = useRouter()

let painelId = ref(Number(route.params.painel_id))
let painelVisaoId = ref(Number(route.params.painelvisao_id))

syncStore
  .fetchSync({
    app: 'painelset',
    model: 'painelvisao',
    id: painelVisaoId.value
  })
  .then((response) => {
    if (response.data.painel !== painelId.value) {
      console.log(painelId, painelVisaoId, response.data)
      // If the painelvisao does not belong to the current painel, redirect to 404
      router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
      return
    }
  })
  .catch((error) => {
    console.error('Error fetching painelvisao:', error)
    router.push({ name: 'painelset_error_404', params: { pathMatch: 'error' } })
  })

const visao = computed(() => {
  return syncStore.data_cache.painelset_painelvisao?.[painelVisaoId.value] || null
})

const trocarVisao = (id) => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'painelvisao',
      id: id
    })
    .then(() => {
      painelVisaoId.value = id
      router.push({ name: 'painelset_painel_visao_view', params: { painelvisao_id: painelVisaoId.value } })
    })
    .catch((error) => {
      console.error('Error activating painelvisao:', error)
    })
}

const ativarVisao = (id) => {
  Resource.Utils.patchModelAction({
    app: 'painelset',
    model: 'painelvisao',
    id: id,
    action: 'activate',
    form: {}
  })
    .then(() => {
      painelVisaoId.value = id
      router.push({ name: 'painelset_painel_visao_view', params: { painelvisao_id: painelVisaoId.value } })
    })
    .catch((error) => {
      console.error('Error activating painelvisao:', error)
    })
}

const visaoAtiva = () => {
  painelVisaoId.value = null
  router
    .push({ name: 'painelset_painel_view', params: { painel_id: painelId.value } })
    .then(() => {
      router.go(0)
    })
}
</script>

<style scoped>
</style>
