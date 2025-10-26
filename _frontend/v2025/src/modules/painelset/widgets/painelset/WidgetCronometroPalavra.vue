<template>
  <div
    :id="`id-widget-cronometro-palavra-${widgetSelected}`"
    ref="widgetCronometroPalavra"
    :key="`widget-cronometro-palavra-${widgetSelected}`"
    class="widget-cronometro-palavra"
  >
    <div
      class="inner-com-a-palavra"
      v-if="individuo_com_a_palavra"
    >
      <div
        class="foto foto-com-a-palavra"
        v-if="individuo_com_a_palavra?.parlamentar || individuo_com_a_palavra?.fotografia"
        :style="`background-image: url(${individuo_com_a_palavra?.fotografia ? fotografiaIndividuoUrl(individuo_com_a_palavra?.id) : fotografiaParlamentarUrl(individuo_com_a_palavra?.parlamentar) } )`"
      >
        <div class="name_individuo">
          <strong>{{ individuo_com_a_palavra?.name }}</strong>
        </div>
      </div>
      <div
        class="foto foto-individuo"
        v-if="!individuo_com_a_palavra?.parlamentar && !individuo_com_a_palavra?.fotografia"
      >
        <FontAwesomeIcon
          icon="user"
          size="1x"
        />
        <div class="name_individuo">
          <strong>{{ individuo_com_a_palavra?.name }}</strong>
        </div>
      </div>
      <div class="inner-cronometro-com-a-palavra">
        <WidgetCronometroBase
          v-if="individuo_com_a_palavra?.cronometro"
          :painel-id="painelId"
          :widget-selected="widgetSelected"
          :cronometro-id="individuo_com_a_palavra?.cronometro"
          display-initial="remaining"
          display-format="mm:ss"
        />
      </div>
    </div>
    <div
      class="inner-aparteante"
      v-if="individuo_aparteante"
    >
      <div
        class="foto foto-aparteante"
        v-if="individuo_aparteante?.parlamentar || individuo_aparteante?.fotografia"
        :style="`background-image: url(${individuo_aparteante?.fotografia ? fotografiaIndividuoUrl(individuo_aparteante?.id) : fotografiaParlamentarUrl(individuo_aparteante?.parlamentar) } )`"
      >
        <div class="name_individuo">
          <strong>{{ individuo_aparteante?.name }}</strong>
        </div>
      </div>
      <div
        class="foto foto-individuo"
        v-if="!individuo_aparteante?.parlamentar && !individuo_aparteante?.fotografia"
      >
        <FontAwesomeIcon
          icon="user"
          size="1x"
        />
        <div class="name_individuo">
          <strong>{{ individuo_aparteante?.name }}</strong>
        </div>
      </div>
      <div class="inner-cronometro-aparteante">
        <WidgetCronometroBase
          v-if="individuo_aparteante?.cronometro"
          :painel-id="painelId"
          :widget-selected="widgetSelected"
          :cronometro-id="individuo_aparteante?.cronometro"
          display-initial="remaining"
          display-format="mm:ss"
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { ref, computed, watch, defineEmits } from 'vue'

import WidgetCronometroBase from './WidgetCronometroBase.vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()

const emit = defineEmits(['oncomponent'])

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  },
  coordsChange: {
    type: Object,
    default: () => ({})
  }
})
// 4. State & Refs
const widgetCronometroPalavra = ref(null)

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const evento = computed(() => {
  return syncStore.data_cache.painelset_evento
    ?.[painel.value?.evento] || null
})

const individuo_com_a_palavra = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return Object.values(syncStore.data_cache.painelset_individuo).find(
      i => i.com_a_palavra && i.evento === evento.value?.id
    ) || null
  }
  return null
})

const individuo_aparteante = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return Object.values(syncStore.data_cache.painelset_individuo).find(
      i => i.aparteado > 0 && i.evento === evento.value?.id
    ) || null
  }
  return null
})

const fotografiaParlamentarUrl = (parlamentar) => {
  if (parlamentar) {
    return '/api/parlamentares/parlamentar/' + parlamentar + '/fotografia.c1024.png'
  }
  return null
}

const fotografiaIndividuoUrl = (individuo) => {
  if (individuo) {
    return '/api/painelset/individuo/' + individuo + '/fotografia.c1024.png'
  }
  return null
}

const syncIndividuos = async () => {
  await syncStore.fetchSync({
    app: 'painelset',
    model: 'individuo',
    params: {
      evento: evento.value?.id || 0
    }
  })
}
syncIndividuos()

// 6. Watchers
watch(individuo_com_a_palavra, (newVal) => {
  emit('oncomponent', {
    type: 'extra_styles',
    extra_styles: {
      'opacity': newVal ? '1.0' : '0'
    }
  })
})

// 7. Events & Lifecycle Hooks
emit('oncomponent', {
  type: 'extra_styles',
  extra_styles: {
    'opacity': authStore.hasPermission('painelset.change_widget') ? '1' : '0'
  }
})

</script>
<style lang="scss" scoped>

.widget-cronometro-palavra {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  overflow: hidden;
  line-height: 1;

  .inner-aparteante, .inner-com-a-palavra {
    position: absolute;
    overflow: hidden;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1em;
  }

  .inner-com-a-palavra {
    top: 2%;
    bottom: 50%;
  }
  .inner-aparteante {
    top: 55%;
    bottom: 2%;
    gap: 0.5em;
    margin-left: 1em;
  }
  .foto-com-a-palavra, .foto-aparteante {
    position: relative;
    height: 100%;
    aspect-ratio: 1 / 1;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    border-radius: 50%;
  }

  .foto-individuo {
    position: relative;
    height: 100%;
    width: auto;
    aspect-ratio: 1 / 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #ccc;
    border-radius: 50%;
  }
  .name_individuo {
    position: absolute;
    font-size: 0.3em;
    bottom: 0em;
    background-color: #444;
    color:#bbb;
    border-radius: 0.4em;
    padding: 0.1em 0.4em;
    white-space: nowrap;
    left: 50%;
    transform: translateX(-50%);

    strong {
      font-size: 1em;
      text-align: center;
      display: block;
    }
    small {
      color: #999;
      font-size: 0.7em;
    }
  }
  .inner-aparteante {
    font-size: 0.9em;
    .name_individuo {
      font-size: 0.25em;
    }
  }
  .inner-cronometro-aparteante {
    font-size: 0.8em;
    color: yellow;
  }
}

</style>
