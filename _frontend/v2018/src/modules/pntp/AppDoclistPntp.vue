<template>
  <div v-if="selected && selectedDocuments.length" class="app-doclist-pntp">
    <div v-if="displayDocs.length" class="row mt-2">
      <div
        v-for="doc in displayDocs"
        :key="doc.id"
        class="col-12 col-sm-12 mb-3"
      >
        <pntp-doclist-item :doc="doc"></pntp-doclist-item>
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
    selectedDocuments () {
      return this.selected && this.selected.documentos ? this.selected.documentos : []
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
