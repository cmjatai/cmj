<template>
  <div v-if="selected" class="app-list-pntp">
    <div class="app-list-pntp__header mb-3">
      <h5 class="app-list-pntp__titulo mb-0">
        <a :href="'/' + selected.slug" class="app-list-pntp__titulo-link">{{ selected.titulo }}</a>
      </h5>
    </div>
    <div v-if="displayItems.length" class="row mt-2">
      <div
        v-for="child in displayItems"
        :key="child.id"
        class="col-12 col-sm-12 mb-3"
      >
        <pntp-list-item
          :item="child"
          :parent_titulo="items[child.parent] ? items[child.parent].titulo : null"
        ></pntp-list-item>
      </div>
    </div>
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
    },
    search: {
      type: String,
      default: ''
    }
  },
  computed: {
    selected () {
      if (!this.selected_id) return null
      return this.items[this.selected_id] || null
    },
    allDescendants () {
      const result = []
      const collect = (ids) => {
        ids.forEach(id => {
          const item = this.items[id]
          if (!item) return
          const hasRenderableChilds = item.childs && item.childs.length > 0
          if (hasRenderableChilds) {
            collect(item.childs)
          } else {
            result.push({ ...item, _parent_titulo: item.parent ? (this.items[item.parent] ? this.items[item.parent].titulo : null) : null })
          }
        })
      }
      if (this.selected && this.selected.childs) collect(this.selected.childs)
      return result
    },
    childItems () {
      if (!this.selected) return []
      if (!this.selected.childs || !this.selected.childs.length) return []
      return this.allDescendants
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
  padding-bottom: 1rem;
  padding-top: 0.3rem;
  display: flex;
  align-items: center;
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

</style>
