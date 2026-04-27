<template>
  <div v-if="selected" class="app-list-pntp">
    <h5 class="app-list-pntp__titulo">
      <a :href="'/' + selected.slug" class="app-list-pntp__titulo-link">{{ selected.titulo }}</a>
    </h5>
    <div v-if="childItems.length" class="row mt-4">
      <div
        v-for="child in childItems"
        :key="child.id"
        class="col-12 col-sm-12 mb-3"
      >
        <pntp-list-item :item="child"></pntp-list-item>
      </div>
    </div>
    <p v-else class="text-muted small">Nenhum item disponível.</p>
  </div>
</template>

<script>
export default {
  name: 'app-list-pntp',
  props: {
    items: {
      type: Object,
      required: true
    },
    selected_id: {
      type: [Number, String],
      default: null
    }
  },
  computed: {
    selected () {
      if (!this.selected_id) return null
      return this.items[this.selected_id] || null
    },
    childItems () {
      if (!this.selected || !this.selected.childs || !this.selected.childs.length) return []
      return this.selected.childs.map(id => this.items[id]).filter(Boolean)
    }
  }
}
</script>

<style lang="scss" scoped>
.app-list-pntp__titulo {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--primary, #007bff);
}

.app-list-pntp__titulo-link {
  color: #343a40;
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}
</style>
