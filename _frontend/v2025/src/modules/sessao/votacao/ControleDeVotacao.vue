<template>
  <div
    :id="`cv-${item.__label__}-${item.id}`"
    :class="[
      'controle-de-votacao',
      item.__label__,
      votacaoAberta ? 'votacao-aberta' : 'votacao-fechada',
      votacaoAberta && authStore.isVotante ? 'votante' : 'observador'
    ]"
  >
    <ProcessoVotacaoDisplay
      :key="`pvd-${item.__label__}-${item.id}`"
      :item="item"
      :sessao="sessao"
      @resync="emit('resync')"
    />
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { ref, watch, computed } from 'vue'
import ProcessoVotacaoDisplay from './ProcessoVotacaoDisplay.vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()

const emit = defineEmits(['resync'])

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  sessao: {
    type: Object,
    required: true
  }
})

const votacaoAberta = computed(() => {
  return (props.item.votacao_aberta &&
    props.item.tipo_votacao !== 4
  )
})


</script>

<style lang="scss">
.controle-de-votacao {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 1;

  &.votante {
    left: 0;
    bottom: 0;
    background-color: #000a;
  }

}

@media screen and (min-width: 768px) {
  .controle-de-votacao {
    // margin: -1em;
  }
}
</style>
