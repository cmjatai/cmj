<template>
  <div
    :id="`is-${item.__label__}-${item.id}`"
    :class="['item-de-sessao', item.__label__, parent ? 'child-item' : 'parent-item']">
    <div class="item-content">
      <ControleDeVotacao
        :key="`cv-${item.__label__}-${item.id}`"
        :item="item"
        :sessao="sessao"
        @resync="emit('resync')"
      />
      <MateriaEmPauta
        :key="`mp-${item.__label__}-${item.id}`"
        :materia-id="item.materia"
        :item="item"
        :sessao="sessao"
        @resync="emit('resync')"
      />
      <ItemDeSessaoControl
        :key="`isc-${item.__label__}-${item.id}`"
        :item="item"
        :sessao="sessao"
      />
    </div>
    <div class="childs">
      <div
        class="title"
        v-if="!item.parent && childs.length > 0"
      >
        <strong>Matérias Anexadas</strong>
      </div>
      <ItemDeSessao
        v-for="child in childs"
        :key="`is-${child.__label__}-${child.id}`"
        :item="child"
        :parent="item"
        :sessao="sessao"
        @resync="emit('resync')"
      />
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import ItemDeSessao from './ItemDeSessao.vue'
import MateriaEmPauta from './MateriaEmPauta.vue'
import ControleDeVotacao from './votacao/ControleDeVotacao.vue'
import ItemDeSessaoControl from './control/ItemDeSessaoControl.vue'
import { computed } from 'vue'

const syncStore = useSyncStore()

const emit = defineEmits(['resync'])

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  parent: {
    type: Object,
    required: false,
    default: null
  },
  sessao: {
    type: Object,
    required: true
  }
})

const childs = computed(() => {
  const allItems = syncStore.data_cache?.[props.item.__label__] || {}
  const childItems = Object.values(allItems).filter(
    item => item.parent === props.item.id
  )
  // ordena pelo campo 'numero_ordem' se existir
  childItems.sort((a, b) => a.numero_ordem - b.numero_ordem)
  return childItems
})

</script>

<style lang="scss">
.item-de-sessao {
  position: relative;
  .item-content {
    position: relative;
    padding: 0.5em;
  }
  &.sessao_expedientemateria {
    z-index: 1;
    background-color: var(--cmj-expmat-background-color);
    .item-content {
      &:hover {
        background-color: var(--cmj-expmat-background-color-hover);
      }
    }
    &::before {
      content: "Grande Expediente";
      position: absolute;
      bottom: 1px;
      right: 5px;
      color: rgba(#777, 0.15);
      font-size: 170%;
      display: inline-block;
      line-height: 1;
      z-index: 1;
    }
  }
  &.sessao_ordemdia {
    z-index: 1;
    background-color: var(--cmj-ordemdia-background-color);
    & > .item-content {
      &:hover {
        background-color: var(--cmj-ordemdia-background-color-hover);
      }
    }
    &::before {
      content: "Ordem do Dia";
      position: absolute;
      bottom: 1px;
      right: 5px;
      color: rgba(#777, 0.15);
      font-size: 170%;
      display: inline-block;
      line-height: 1;
      z-index: 0;
    }
  }
  &.parent-item {
    margin: 0.5em;
  }
  .childs {
    font-size: 0.8em;
    & > .title {
      font-size: 1.8em;
      display: inline-block;
      padding: 0.2em 1em;
      color: var(--bs-light);
      background-color: var(--bs-dark);
    }
  }
}

@media screen and (min-width: 768px) {
  .item-de-sessao {
    &.parent-item {
      margin: 1em;
    }
    .item-content {
      padding: 1em;
    }
  }
}
</style>
