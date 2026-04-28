<template>
  <div v-if="selected" class="app-list-pntp">
    <div class="app-list-pntp__header d-flex align-items-center mb-3">
      <h5 class="app-list-pntp__titulo mb-0 flex-grow-1">
        <a :href="'/' + selected.slug" class="app-list-pntp__titulo-link">{{ selected.titulo }}</a>
      </h5>
      <div class="app-list-pntp__search-wrap ml-3">
        <input
          v-model="search"
          type="search"
          class="form-control form-control-sm app-list-pntp__search"
          placeholder="Buscar..."
        />
        <i class="fa fa-search app-list-pntp__search-icon"></i>
      </div>
    </div>
    <div v-if="displayItems.length" class="row mt-2">
      <div
        v-for="child in displayItems"
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
  data () {
    return {
      search: ''
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
    },
    displayItems () {
      const term = this.search.trim().toLowerCase()
      if (!term) return this.childItems
      return Object.values(this.items).filter(item =>
        item.titulo && item.titulo.toLowerCase().includes(term)
      )
    }
  }
}
</script>

<style lang="scss" scoped>
.app-list-pntp__header {
  border-bottom: 2px solid var(--primary, #007bff);
  padding-bottom: 0.5rem;
  padding-top: 0.3rem;
}

.app-list-pntp__titulo {
  font-size: 1rem;
  font-weight: 600;
}

.app-list-pntp__titulo-link {
  color: #343a40;
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}

.app-list-pntp__search-wrap {
  position: relative;
  max-width: 200px;
}

.app-list-pntp__search {
  padding-right: 1.8rem;
}

.app-list-pntp__search-icon {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: #adb5bd;
  pointer-events: none;
}
</style>
