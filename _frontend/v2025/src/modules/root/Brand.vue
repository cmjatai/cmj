<template>
  <div class="inner-brand">
    <a class="link-logo" href="/">
      <img :src="casa.logotipo !== undefined ? casa.logotipo : '~@/assets/img/brasao_transp.gif'"/>
    </a>
    <a class="link-nome" href="/">
      <span class="title-brand">
        {{ casa.nome }}<br>
        <small>PortalCMJ</small>
      </span>
    </a>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed, onMounted } from 'vue'

const syncStore = useSyncStore()

const casa = computed(() => {
  return Object.values(
    syncStore.data_cache?.base_casalegislativa ?? {}
  )[0] ?? {}
})

onMounted(() => {
  syncStore.fetchSync({
    app: 'base',
    model: 'casalegislativa',
    orderBy: 'id',
    limit: 1
  })
})

</script>
<style lang="scss">
.inner-brand {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 0.5em;
  img {
    height: 3em;
    padding: 0.2em;
  }
  .link-logo {
    flex: 0 0 0;
  }
  .link-nome {
    flex: 1 0 0;
  }
}

</style>
