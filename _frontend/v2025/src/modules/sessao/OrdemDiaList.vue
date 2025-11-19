<template>
  <div class="ordemdia-list">
    <div class="title">
      <strong>Matérias da Ordem do Dia</strong>
      <FontAwesomeIcon
        icon="arrows-rotate"
        class="resync-icon-ordemdia cursor-pointer ms-2"
        title="Recarregar matéria"
        @click="rotateAndEmitResync"
      />
    </div>
    <div class="ordemdia-content">
      <ItemDeSessao
        :key="`is-${ordem.__label__}-${ordem.id}`"
        v-for="ordem in ordemDiaList"
        :item="ordem"
        :sessao="sessao"
        @resync="emit('resync')"
      />
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'
import ItemDeSessao from './ItemDeSessao.vue'

const emit = defineEmits(['resync'])

const syncStore = useSyncStore()

const props = defineProps({
  sessao: {
    type: Object,
    required: true
  }
})

const ordemDiaList = computed(() => {
  const allOrdemDias = syncStore.data_cache?.sessao_ordemdia || {}
  const ordemDiasForSessao = Object.values(
    allOrdemDias
  ).filter(
    ordemDia => ordemDia.sessao_plenaria === props.sessao?.id && ordemDia.parent === null
  )
  // ordena pelo campo 'numero_ordem' se existir
  ordemDiasForSessao.sort((a, b) => a.numero_ordem - b.numero_ordem)
  return ordemDiasForSessao
})

const rotateAndEmitResync = () => {
  emit('resync')
  // Adiciona a animação de rotação
  const icon = document.querySelector('.resync-icon-ordemdia')
  if (icon) {
    icon.classList.add('rotate')
    setTimeout(() => {
      icon.classList.remove('rotate')
    }, 1000)
  }
}

</script>

<style lang="scss">
.ordemdia-list {
  display: flex;
  flex-direction: column;
  gap: 0.5em;

  .ordemdia-content {
    display: flex;
    flex-direction: column;
    gap: 0.5em;
  }
  & > .title {
    display: flex;
    background-color: var(--bs-body-bg);
    justify-content: space-between;
    align-items: center;
    padding: 0.5em;
    strong {
      font-size: 1.1em;
      color: var(--bs-primary);
    }
  }
  .resync-icon-ordemdia {
    opacity: 0.5;
    transition: opacity 0.3s ease;
    &:hover {
      opacity: 1.0;
    }
    @keyframes rotation-ordemdia {
      0% {
        transform: rotate(0deg);
      }
      40% {
        transform: rotate(360deg);
      }
      100% {
        transform: rotate(720deg);
      }
    }
    &.rotate {
      animation: rotation-ordemdia 1s infinite ease;
    }
  }
}

@media screen and (min-width: 768px) {
  .ordemdia-list {
    display: flex;
    flex-direction: column;
    gap: 1em;
    .ordemdia-content {
      display: flex;
      flex-direction: column;
      gap: 1em;
    }
    & > .title {
      padding: 1em;
      strong {
        font-size: 2em;
      }
    }
  }
}
</style>
