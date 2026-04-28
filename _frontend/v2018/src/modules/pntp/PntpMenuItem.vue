<template>
  <li :class="['pntp-menu__item', { 'pntp-menu__item--active': isActive }]">
    <div class="pntp-menu__item-header d-flex align-items-center justify-content-between">
      <span
        :class="['pntp-menu__link', 'flex-grow-1', { 'active font-weight-bold': isActive }]"
        @click="onSelect"
      >{{ item.titulo }}</span>
      <button
        v-if="childsWithChildren.length"
        class="pntp-menu__toggle btn btn-link btn-sm p-0 ml-2 text-secondary"
        :title="open ? 'Recolher' : 'Expandir'"
        @click.stop="open = !open"
      >
        <i :class="open ? 'fa fa-chevron-up' : 'fa fa-chevron-down'"></i>
      </button>
    </div>
    <ul
      v-if="item.childs && item.childs.length && open"
      class="pntp-menu__sublist list-unstyled pl-3 mt-1"
    >
      <pntp-menu-item
        v-for="childId in childsWithChildren"
        :key="childId"
        :item="items[childId]"
        :items="items"
        :selected_id="selected_id"
        @select="$emit('select', $event)"
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
    selected_id: {
      type: [Number, String],
      default: null
    }
  },
  data () {
    return {
      open: false
    }
  },
  computed: {
    isActive () {
      return this.selected_id !== null && String(this.item.id) === String(this.selected_id)
    },
    childsWithChildren () {
      if (!this.item.childs) return []
      return this.item.childs.filter(id => {
        const child = this.items[id]
        return child && child.childs && child.childs.length > 0
      })
    },
    isInSelectedPath () {
      if (!this.selected_id) return false
      let current = this.items[this.selected_id]
      while (current) {
        if (String(current.id) === String(this.item.id)) return true
        if (current.parent === null || current.parent === undefined) break
        current = this.items[current.parent]
      }
      return false
    }
  },
  methods: {
    onSelect () {
      this.$emit('select', this.item.id)
    }
  },
  created () {
    this.open = this.isInSelectedPath
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
  cursor: pointer;

  &:hover {
    color: var(--primary, #007bff);
  }
}

.pntp-menu__sublist {
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  padding-left: 0.75rem !important;
}

.pntp-menu__toggle {
  line-height: 1;
  font-size: 0.75rem;
}
</style>
