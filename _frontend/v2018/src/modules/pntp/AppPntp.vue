<template>
  <div class="app-pntp mt-4 mb-4">
    <message></message>
    <slot></slot>
    <div v-if="pntp_data" class="row">
      <div class="col-md-4">
        <app-menu-pntp
          v-bind:items="pntp_data.items"
          v-bind:selected_id="selected_id"
          v-bind:parent_slug="pntp_data.parent_slug"
          v-bind:parent_title="pntp_data.parent_title"
          @select="onSelect"
        ></app-menu-pntp>
      </div>
      <div class="col-md-8">
        <div class="app-pntp__search-wrap mt-1 mt-md-0">
          <input
            v-model="search"
            type="search"
            class="form-control form-control-sm app-pntp__search"
            placeholder="Buscar..."
          />
          <i class="fa fa-search app-pntp__search-icon"></i>
        </div>
        <app-list-pntp
          v-bind:items="pntp_data.items"
          v-bind:selected_id="selected_id"
          v-bind:search="search"
          v-bind:root_slug="pntp_data.root ? pntp_data.root.slug : ''"
        ></app-list-pntp>
        <app-doclist-pntp
          v-bind:items="pntp_data.items"
          v-bind:selected_id="selected_id"
          v-bind:search="search"
          v-bind:root_slug="pntp_data.root ? pntp_data.root.slug : ''"
        ></app-doclist-pntp>
        <p v-if="selectedIsEmpty" class="text-muted small mt-2">Nenhum item disponível.</p>
      </div>
    </div>
  </div>
</template>
<script>
import Message from '@/components/utils/message/Message'
export default {
  name: 'app-pntp',
  components: {
    Message
  },
  props: {
    classe_id: {
      type: [Number, String],
      required: true
    }
  },
  data () {
    return {
      pntp_data: null,
      selected_id: null,
      search: ''
    }
  },
  computed: {
    selectedIsEmpty () {
      if (!this.pntp_data || !this.selected_id) return false
      const item = this.pntp_data.items[this.selected_id]
      if (!item) return false
      const hasChilds = item.childs && item.childs.length > 0
      const hasDocs = item.documentos && item.documentos.length > 0
      return !hasChilds && !hasDocs
    }
  },
  methods: {
    onSelect (id) {
      this.selected_id = id
      this.search = ''
      const url = new URL(window.location.href)
      url.searchParams.set('categoria', id)
      window.history.pushState({ categoria: id }, '', url.toString())
    }
  },
  mounted () {
    this.loginStatus()
    let data = JSON.parse(document.getElementById('pntp-data').textContent)
    this.pntp_data = data

    const params = new URLSearchParams(window.location.search)
    const categoriaParam = params.get('categoria')

    if (categoriaParam && data.items[categoriaParam]) {
      this.selected_id = Number(categoriaParam)
    } else {
      this.selected_id = data.active_item
        ? data.active_item.id
        : (Object.values(data.items).find(i => i.parent === null) || {}).id || null
    }

    window.addEventListener('popstate', (e) => {
      const id = e.state && e.state.categoria
        ? e.state.categoria
        : new URLSearchParams(window.location.search).get('categoria')
      if (id && this.pntp_data.items[id]) {
        this.selected_id = Number(id)
      }
    })
  }
}
</script>
<style lang="scss" scoped>
.app-pntp__search-wrap {
  position: absolute;
  right: 1rem;
}

.app-pntp__search {
  padding-right: 1.8rem;
}

.app-pntp__search-icon {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: #adb5bd;
  pointer-events: none;
}

</style>
