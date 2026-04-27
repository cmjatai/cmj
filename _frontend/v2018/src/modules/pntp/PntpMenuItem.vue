<template>
  <li :class="['pntp-menu__item', { 'pntp-menu__item--active': item.active === 'active' }]">
    <div class="pntp-menu__item-header d-flex align-items-center justify-content-between">
      <a
        :href="'/' + item.slug"
        :class="['pntp-menu__link', 'flex-grow-1', { 'active font-weight-bold': item.active === 'active' }]"
      >{{ item.titulo }}</a>
      <button
        v-if="item.childs && item.childs.length"
        class="pntp-menu__toggle btn btn-link btn-sm p-0 ml-2 text-secondary"
        :title="open ? 'Recolher' : 'Expandir'"
        @click.prevent="open = !open"
      >
        <i :class="open ? 'fa fa-chevron-up' : 'fa fa-chevron-down'"></i>
      </button>
    </div>
    <ul
      v-if="item.childs && item.childs.length && open"
      class="pntp-menu__sublist list-unstyled pl-3 mt-1"
    >
      <pntp-menu-item
        v-for="childId in item.childs"
        :key="childId"
        :item="items[childId]"
        :items="items"
        :active_item="active_item"
      ></pntp-menu-item>
    </ul>
  </li>
</template>

<script>
export default {
  name: 'pntp-menu-item',
  props: {
    item: {
      type: Object,
      required: true
    },
    items: {
      type: Object,
      required: true
    },
    active_item: {
      type: Object,
      default: null
    }
  },
  data () {
    return {
      open: false
    }
  },
  computed: {
    isInActivePath () {
      if (!this.active_item) return false
      let current = this.active_item
      while (current) {
        if (current.id === this.item.id) return true
        if (current.parent === null || current.parent === undefined) break
        current = this.items[current.parent]
      }
      return false
    }
  },
  created () {
    this.open = this.isInActivePath || this.item.active === 'active'
  }
}
</script>

<style lang="scss" scoped>
.pntp-menu__item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);

  &:last-child {
    border-bottom: none;
  }

  &--active > .pntp-menu__item-header > .pntp-menu__link {
    color: var(--primary, #007bff);
  }
}

.pntp-menu__item-header {
  padding: 0.35rem 0;
}

.pntp-menu__link {
  font-size: 0.9rem;
  color: #343a40;
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}

.pntp-menu__sublist {
  border-left: 2px solid rgba(0, 0, 0, 0.08);
  padding-left: 0.75rem !important;
}

.pntp-menu__toggle {
  line-height: 1;
  font-size: 0.75rem;
}
</style>
