<template>
  <nav v-if="root" class="pntp-menu">
    <h5 class="pntp-menu__titulo">
      <a :href="'/' + root.slug" class="pntp-menu__titulo-link">{{ root.titulo }}</a>
    </h5>
    <ul v-if="root.childs && root.childs.length" class="pntp-menu__list list-unstyled mt-2 mb-0">
      <pntp-menu-item
        v-for="childId in root.childs"
        :key="childId"
        :item="items[childId]"
        :items="items"
        :active_item="active_item"
      ></pntp-menu-item>
    </ul>
  </nav>
</template>

<script>
export default {
  name: 'app-menu-pntp',
  props: {
    items: {
      type: Object,
      required: true
    },
    active_item: {
      type: Object,
      default: null
    }
  },
  computed: {
    root () {
      return Object.values(this.items).find(item => item.parent === null) || null
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-menu {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 1rem;
}

.pntp-menu__titulo {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--primary, #007bff);
}

.pntp-menu__titulo-link {
  color: #343a40;
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}

.pntp-menu__list {
  margin: 0;
  padding: 0;
}
</style>
