<template>
  <div class="pcl-lista-emendas-ajustes">
    <h6 class="pcl-lista-header">
      Emendas e Ajustes
      <small class="text-muted">({{ items.length }})</small>
      <b-spinner v-if="fetching" small variant="secondary" class="ml-1"></b-spinner>
    </h6>
    <div class="list-group">
      <a href="#"
        v-for="item in items"
        :key="`${item.__label__}_${item.id}`"
        class="list-group-item list-group-item-action py-2"
        :class="{ active: isSelected(item) }"
        @click.prevent="$emit('select', item)"
      >
        <div class="d-flex justify-content-between align-items-start">
          <div class="flex-grow-1 mr-2">
            <b-badge :variant="itemBadgeVariant(item)" class="mr-1">
              {{ itemBadgeLabel(item) }}
            </b-badge>
            <b-badge v-if="isEmenda(item)" :variant="faseVariant(item.fase)" class="mr-1">
              {{ faseLabel(item.fase) }}
            </b-badge>
            <div class="mt-1 small">{{ item.__str__ }}</div>
            <div class="mt-1 small">{{ item.descricao }}</div>
          </div>
        </div>
      </a>
    </div>
  </div>
</template>

<script>
import {
  faseVariant,
  faseLabel,
  itemBadgeVariant,
  itemBadgeLabel,
  isEmenda
} from './utils/pcl-helpers'

export default {
  name: 'pcl-lista-emendas-ajustes',
  props: {
    items: {
      type: Array,
      default: () => []
    },
    registroSelecionado: {
      type: Object,
      default: null
    },
    fetching: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    faseVariant,
    faseLabel,
    itemBadgeVariant,
    itemBadgeLabel,
    isEmenda,
    isSelected (item) {
      return this.registroSelecionado &&
        this.registroSelecionado.id === item.id &&
        this.registroSelecionado.__label__ === item.__label__
    }
  }
}
</script>

<style lang="scss" scoped>
$border-color: rgba(0, 0, 0, 0.125);

.pcl-lista {
  &-header {
    background-color: #f8f9fa;
    border: 1px solid $border-color;
    border-bottom: none;
    border-radius: 0.25rem 0.25rem 0 0;
    padding: 0.4rem 0.75rem;
    margin-bottom: 0;
    font-weight: 600;
    line-height: 1.6;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-variant: small-caps;
  }

  &-emendas-ajustes {
    .list-group {
      .list-group-item:first-child {
        border-top: 0;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
      }
    }

    .list-group-item.active {
      z-index: 0;
    }

    @media (max-width: 767.98px) {
      max-height: 50vh;
      overflow-y: auto;
      margin-bottom: 1em;
    }
  }
}
</style>
