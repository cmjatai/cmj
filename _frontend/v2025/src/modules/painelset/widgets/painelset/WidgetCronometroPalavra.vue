<template>
  <div
    class="widget-cronometro-palavra"
  >
    <div class="inner-com-a-palavra" v-if="individuo_com_a_palavra">
      <div
        class="foto foto-com-a-palavra" v-if="individuo_com_a_palavra?.parlamentar"
        :style="`background-image: url(${fotografiaParlamentarUrl(individuo_com_a_palavra?.parlamentar)})`"
      >
        <div class="name_individuo">
          <small>Com a Palavra: </small><br>
          <strong>{{ individuo_com_a_palavra?.name }}</strong>
        </div>
      </div>
      <div class="foto foto-individuo" v-if="!individuo_com_a_palavra?.parlamentar">
        <FontAwesomeIcon icon="user" size="1x" />
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
    <div class="inner-aparteante" v-if="individuo_aparteante">
      <div
        class="foto foto-aparteante"
        :style="`background-image: url(${fotografiaParlamentarUrl(individuo_aparteante?.parlamentar)})`"
        >
        <div class="name_individuo">
          <small>Em Aparte: </small><br>
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
import { computed, watch, defineEmits } from 'vue'

import WidgetCronometroBase from './WidgetCronometroBase.vue'

const syncStore = useSyncStore()

const emit = defineEmits(['oncomponent'])

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  }
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const evento = computed(() => {
  return syncStore.data_cache.painelset_evento
    ?.[painel.value?.evento] || null
})

const individuo_com_a_palavra = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return Object.values(syncStore.data_cache.painelset_individuo).find(i => i.com_a_palavra) || null
  }
  return null
})

const individuo_aparteante = computed(() => {
  if (syncStore.data_cache?.painelset_individuo) {
    return Object.values(syncStore.data_cache.painelset_individuo).find(i => i.aparteado > 0) || null
  }
  return null
})

const fotografiaParlamentarUrl = (parlamentar) => {
  if (parlamentar) {
    return '/api/parlamentares/parlamentar/' + parlamentar + '/fotografia.c1024.png'
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

watch(individuo_com_a_palavra, (newVal) => {
  emit('oncomponent', {
    type: 'extra_styles',
    extra_styles: {
      'opacity': newVal ? '1.0' : '0'
    }
  })
})

</script>
<style lang="scss" scoped>
  .widget-cronometro-palavra {
    display: flex;
    height: 100%;
    flex-direction: column;
    line-height: 1;

    .inner-aparteante, .inner-com-a-palavra {
      display: flex;
      align-items: center;
    }

    .inner-com-a-palavra {
      flex: 0 0 55%;
      justify-content: space-evenly;
    }
    .inner-aparteante {
      flex: 0 0 45%;
      justify-content: center;
      margin-left: 10%;
      gap: 0.3em;
      // margin-top: -0.6em;
    }

    .widget-cronometro-base {
      flex: 0 0 0%;
    }
    .foto-com-a-palavra, .foto-aparteante {
      height: 100%;
      width: auto;
      aspect-ratio: 1 / 1;
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      border-radius: 50%;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }
    .foto-individuo {
      height: 100%;
      width: auto;
      aspect-ratio: 1 / 1;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #ccc;
      border-radius: 50%;
    }
    .inner-cronometro-com-a-palavra {
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      align-items: flex-end;
      height: 100%;
    }
    .inner-cronometro-aparteante {
      font-size: 0.75em;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      align-items: flex-end;
      height: 100%;

    }
    .foto-aparteante {
      margin-right: 0.2em;
    }

    .name_individuo {
      display: inline-block;
      font-size: 0.12em;
      text-align: left;
      padding: 0em 0.4em 0.3em;
      white-space: nowrap;
      background-color: #ffffffef;
      color:#444;
      border-radius: 0.3em;
      small {
        color: #999;
        font-size: 0.7em;
      }
      strong {
        font-size: 1em;
      }
    }
  }

</style>
