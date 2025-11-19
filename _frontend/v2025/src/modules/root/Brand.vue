<template>
  <div class="inner-brand">
    <a class="link-logo" href="/">
      <img :src="casa.logotipo !== undefined ? casa.logotipo : '/static/imgs/brasao_transp.gif'"/>
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
    params: {
      o: 'id'
    }
  })
})

</script>
<style lang="scss">

.inner-brand {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 0.1em;
  img {
    height: 1.8em;
    margin-right: 0.5em;
  }
  .link-logo {
    flex: 0 0 0;
  }
  .link-nome {
    flex: 1 0 0;
    font-size: 0.75em;
  }
}

@media screen and (min-width: 480px) {
  .inner-brand {
    .link-nome {
      font-size: 0.95em;
    }
    img {
      height: 2em;
    }
  }
}

@media screen and (min-width: 768px) {
  .inner-brand {
    .link-nome {
      font-size: 1.3em;
    }
    img {
      height: 2.5em;
      margin: 0 0.7em;
    }
  }
}

</style>
