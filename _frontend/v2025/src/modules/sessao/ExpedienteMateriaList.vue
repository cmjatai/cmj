<template>
  <div class="expediente-materia-list">
    <div class="title">
      <strong>Matérias do Grande Expediente</strong>
      <FontAwesomeIcon
        icon="arrows-rotate"
        class="resync-icon-expmateria cursor-pointer ms-2"
        title="Recarregar matéria"
        @click="rotateAndEmitResync"
      />
    </div>
    <div class="expediente-materia-content">
      <ItemDeSessao
        :key="`is-${expmat.__label__}-${expmat.id}`"
        v-for="expmat in expedienteMateriaList"
        :item="expmat"
        :sessao="sessao"
        @resync="emit('resync')"
      />
      <div class="expedientemateria empty alert alert-info" v-if="expedienteMateriaList.length === 0">
        Nenhuma matéria cadastrada no grande expediente.
      </div>
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

const expedienteMateriaList = computed(() => {
  const allExps = syncStore.data_cache?.sessao_expedientemateria || {}
  const expedienteForSessao = Object.values(allExps).filter(
    expmat => expmat.sessao_plenaria === props.sessao?.id && expmat.parent === null
  )
  // ordena pelo campo 'numero_ordem' se existir
  expedienteForSessao.sort((a, b) => a.numero_ordem - b.numero_ordem)
  return expedienteForSessao
})

const rotateAndEmitResync = () => {
  emit('resync')
  // Adiciona a animação de rotação
  const icon = document.querySelector('.resync-icon-expmateria')
  if (icon) {
    icon.classList.add('rotate')
    setTimeout(() => {
      icon.classList.remove('rotate')
    }, 1000)
  }
}

</script>

<style lang="scss">
.expediente-materia-list {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
  .expediente-materia-content {
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
  .resync-icon-expmateria {
    opacity: 0.5;
    transition: opacity 0.3s ease;
    &:hover {
      opacity: 1.0;
    }
    @keyframes rotation-expmateria {
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
      animation: rotation-expmateria 1s infinite ease;
    }
  }
}

@media screen and (min-width: 768px) {
  .expediente-materia-list {
    display: flex;
    flex-direction: column;
    gap: 1em;
    .expediente-materia-content {
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
