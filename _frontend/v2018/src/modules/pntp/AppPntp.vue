<template>
  <div class="app-pntp mt-4 mb-4">
    <message></message>
    <slot></slot>
    <div ref="stickysentinel" class="app-pntp__sentinel"></div>
    <div v-if="pntp_data" class="row">
      <div class="col-md-auto app-pntp__menu-col" ref="menuCol">
        <app-menu-pntp
          v-bind:items="pntp_data.items"
          v-bind:selected_id="selected_id"
          v-bind:parent_slug="pntp_data.parent_slug"
          v-bind:parent_title="pntp_data.parent_title"
          @select="onSelect"
        ></app-menu-pntp>
      </div>
      <div class="col bg_mobile">
        <div class="app-pntp__search-wrap mt-1 mt-md-0">
          <input
            v-model="search"
            type="search"
            name="search"
            class="form-control app-pntp__search"
            :placeholder="`Buscar em ${pntp_data.root.titulo}...`"
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
  watch: {
    search (val) {
      const url = new URL(window.location.href)
      if (val) {
        url.searchParams.set('search', val)
      } else {
        url.searchParams.delete('search')
      }
      window.history.replaceState(
        { categoria: this.selected_id, search: val },
        '',
        url.toString()
      )
    }
  },
  methods: {
    onSelect (id) {
      this.selected_id = id
      this.search = ''
      const url = new URL(window.location.href)
      url.searchParams.set('categoria', id)
      url.searchParams.delete('search')
      window.history.pushState({ categoria: id, search: '' }, '', url.toString())
    }
  },
  mounted () {
    this.loginStatus()
    let data = JSON.parse(document.getElementById('pntp-data').textContent)
    this.pntp_data = data

    const params = new URLSearchParams(window.location.search)
    const categoriaParam = params.get('categoria')
    const searchParam = params.get('search')

    if (categoriaParam && data.items[categoriaParam]) {
      this.selected_id = Number(categoriaParam)
    } else {
      this.selected_id = data.active_item
        ? data.active_item.id
        : (Object.values(data.items).find(i => i.parent === null) || {}).id || null
    }

    if (searchParam) {
      this.search = searchParam
    }

    window.addEventListener('popstate', (e) => {
      const id = e.state && e.state.categoria
        ? e.state.categoria
        : new URLSearchParams(window.location.search).get('categoria')
      if (id && this.pntp_data.items[id]) {
        this.selected_id = Number(id)
      }
      const s = e.state && e.state.search !== undefined
        ? e.state.search
        : (new URLSearchParams(window.location.search).get('search') || '')
      this.search = s
    })

    this._stickyObserver = new IntersectionObserver(
      ([entry]) => {
        this.$refs.menuCol.classList.toggle('app-pntp__menu-col--stuck', !entry.isIntersecting)
      },
      { threshold: 0 }
    )
    this._stickyObserver.observe(this.$refs.stickysentinel)
  },
  beforeDestroy () {
    if (this._stickyObserver) this._stickyObserver.disconnect()
  }
}
</script>
<style lang="scss" scoped>
.app-pntp__sentinel {
  height: 0;
  visibility: hidden;
}

.app-pntp__menu-col {
  position: sticky;
  top: 0;
  align-self: flex-start;
  max-height: 100vh;
  overflow-y: hidden;

  &.app-pntp__menu-col--stuck {
    overflow-y: auto;
  }
}

.app-pntp__search-wrap {
  position: absolute;
  top: 0.25rem;
  right: 1rem;
  min-width: 30vw;
}

.app-pntp__search {
  padding: 0.5rem 0.75rem;
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

@media screen and (max-width: 767.98px) {
  .app-pntp__search-wrap {
    position: static;
    margin-bottom: 0.75rem;
  }
  .bg_mobile {
    background: #f7f7f7 url(~@/assets/img/bg.png);
    padding: 1rem 0.75rem;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin: 1rem;
  }
  .app-pntp__menu-col {
    position: relative;
    max-height: 200vh;
    overflow-y: hidden;
    &.app-pntp__menu-col--stuck {
      overflow-y: hidden;
    }
  }
}

</style>
