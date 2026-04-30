<template>
  <div v-if="selected" class="app-list-pntp">
    <div class="app-list-pntp__header mb-3">
      <i :class="['fa', selected.icon_classe || '']"></i>
      <h2 class="app-list-pntp__titulo mb-0 pr-5">
        <a :href="'/' + selected.slug" class="app-list-pntp__titulo-link">{{ selected.titulo }}</a>
      </h2>
    </div>
    <div v-if="displayItems.length" class="row mt-3">
      <div
        v-for="child in displayItems"
        :key="child.id"
        class="col-12 col-sm-12 mb-3"
      >
        <pntp-list-item
          :item="child"
          :parent_titulo="items[child.parent] ? items[child.parent].titulo : null"
          :root_slug="root_slug"
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
    },
    root_slug: {
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
      return Object.values(this.items).filter(item => {
        const isLeaf = !item.childs || item.childs.length === 0
        return isLeaf && item.titulo && item.titulo.toLowerCase().includes(term)
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.app-list-pntp__header {
  padding-top: 0.3rem;
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  i {
    color: var(--primary, #007bff);
    font-size: 1.5rem;
  }
  .icon {
    height: 2rem;
    width: 2rem;
    border-radius: 4px;
    padding: 0.5rem;
    &.icon-transparencia {
      background-color: var(--primary, #007bff);
      i {
        color: #fff;
      }
    }
  }
}

.app-list-pntp__titulo {
  font-size: 1.2rem;
  font-weight: 700;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid var(--primary, #007bff);
}

.app-list-pntp__titulo-link {
  color: var(--primary, #007bff);
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}

</style>
