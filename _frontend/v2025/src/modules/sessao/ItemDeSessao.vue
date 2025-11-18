<template>
  <div
    :id="`is-${item.__label__}-${item.id}`"
    :class="['item-de-sessao', item.__label__, parent ? 'child-item' : 'parent-item']"
  >
    <div
      @click.self="focusOnTop"
      :id="`item-content-${item.__label__}-${item.id}`"
      :class="[
        'item-content',
        item.votacao_aberta && item.tipo_votacao === 2 ? 'votacao-nominal' : '',
        userIsAdminSessao ? 'item-admin' : '',
        userIsAdminSessao && possuiRegistroVotacao.length > 0 ? `possui-registro-votacao-${possuiRegistroVotacao.length}` : ''
      ]"
    >
      <ItemDeSessaoAdmin
        :key="`is-admin-${item.__label__}-${item.id}`"
        :item="item"
        :sessao="sessao"
        @resync="emit('resync')"
      />
      <ControleDeVotacao
        :key="`cv-${item.__label__}-${item.id}`"
        :item="item"
        :sessao="sessao"
        @resync="emit('resync')"
      />
      <MateriaEmPauta
        @click.self="focusOnTop"
        :key="`mp-${item.__label__}-${item.id}`"
        :materia-id="item.materia"
        :item="item"
        :sessao="sessao"
        @resync="emit('resync')"
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
import { useAuthStore } from '~@/stores/AuthStore'
import ItemDeSessao from './ItemDeSessao.vue'
import MateriaEmPauta from './MateriaEmPauta.vue'
import ControleDeVotacao from './votacao/ControleDeVotacao.vue'
import ItemDeSessaoAdmin from './admin/ItemDeSessaoAdmin.vue'
import { computed } from 'vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()

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

const userIsAdminSessao = computed(() => {
  return authStore.hasPermission('sessao.add_sessaoplenaria')
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

const focusOnTop = () => {
  const element = document.getElementById(`item-content-${props.item.__label__}-${props.item.id}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const possuiRegistroVotacao = computed(() => {
  const field = props.item.__label__ === 'sessao_ordemdia' ? 'ordem' : 'expediente'
  return Object.values(syncStore.data_cache?.sessao_registrovotacao || {}).filter(
    rv => rv[field] === props.item.id
  )
})

</script>

<style lang="scss">
.item-de-sessao {
  position: relative;
  .item-de-sessao-admin {
    .btn {
      opacity: 0.2;
    }
  }
  &:hover .item-de-sessao-admin {
    .btn {
      opacity: 1;
    }
  }
  .item-content {
    position: relative;
    padding: 1.5em 0.5em;
    padding-bottom: 1.5em;
    &.votacao-nominal {
      min-height: 60vh;
    }
    &.item-admin {
      min-height: calc(70vh);
      transition: all 0.3s ease;
      &.possui-registro-votacao-1, &.possui-registro-votacao-2, &.possui-registro-votacao-3 {
        background-color: #4bc56633;
        min-height: auto;
        zoom: 0.8;
      }
      &.possui-registro-votacao-2 {
        zoom: 0.7;
        .materia-em-pauta {
          .inner-materia {
            // display: none;
          }
        }
      }
      &.possui-registro-votacao-3 {
        zoom: 0.333;
      }
    }
  }
  &.sessao_expedientemateria {
    z-index: 1;
    background-color: var(--cmj-expmat-background-color);
    & > .item-content {
      min-height: auto;
    }
    &.item-admin {
      &:hover {
        background-color: var(--cmj-expmat-background-color-hover);
        &.possui-registro-votacao {
          background-color: #4bc56633;
        }
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
      z-index: 0;
    }
  }
  &.sessao_ordemdia {
    z-index: 1;
    background-color: var(--cmj-ordemdia-background-color);
    & > .item-content {
      &:hover {
        background-color: var(--cmj-ordemdia-background-color-hover);
        &.possui-registro-votacao {
          background-color: #4bc56633;
        }
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
      padding: 1.5em 1em;
    }
  }
}
</style>
