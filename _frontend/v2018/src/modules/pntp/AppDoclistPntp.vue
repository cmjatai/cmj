<template>
  <div v-if="selected && selectedDocuments.length" class="app-doclist-pntp">
    <div v-if="displayDocs.length" class="row mt-2">
      <div
        v-for="doc in displayDocs"
        :key="doc.id"
        class="col-12 col-sm-12 mb-3"
      >
        <pntp-doclist-item
          :doc="doc"
          :parent_titulo="doc._parent_titulo || null"
          :parent_slug="doc._parent_slug || ''"
        ></pntp-doclist-item>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'app-doclist-pntp',
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
    allDescendantDocs () {
      const result = []
      const collect = (item) => {
        const hasChilds = item.childs && item.childs.length > 0
        if (!hasChilds) {
          if (item.documentos && item.documentos.length) {
            item.documentos.forEach(doc => result.push({ ...doc, _parent_titulo: item.titulo, _parent_slug: item.slug }))
          }
        } else {
          item.childs.forEach(id => {
            const child = this.items[id]
            if (child) collect(child)
          })
        }
      }
      if (this.selected) collect(this.selected)
      return result
    },
    selectedDocuments () {
      if (!this.selected) return []
      return this.allDescendantDocs
    },
    displayDocs () {
      const term = this.search.trim().toLowerCase()
      if (!term) return this.selectedDocuments
      return this.selectedDocuments.filter(doc =>
        doc.titulo && doc.titulo.toLowerCase().includes(term)
      )
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
