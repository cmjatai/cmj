<template>
  <div class="app-pntp container mt-4 mb-4">
    <slot></slot>
    <div v-if="ptnp_data" class="row">
      <div class="col-md-4">
        <app-menu-pntp
          v-bind:items="ptnp_data.items"
          v-bind:selected_id="selected_id"
          v-bind:parent_slug="ptnp_data.parent_slug"
          v-bind:parent_title="ptnp_data.parent_title"
          @select="onSelect"
        ></app-menu-pntp>
      </div>
      <div class="col-md-8">
        <app-list-pntp
          v-bind:items="ptnp_data.items"
          v-bind:selected_id="selected_id"
        ></app-list-pntp>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'app-pntp',
  props: {
    classe_id: {
      type: [Number, String],
      required: true
    }
  },
  data () {
    return {
      ptnp_data: null,
      selected_id: null
    }
  },
  methods: {
    onSelect (id) {
      this.selected_id = id
    }
  },
  mounted () {
    let data = JSON.parse(document.getElementById('pntp-data').textContent)
    this.ptnp_data = data
    this.selected_id = data.active_item
      ? data.active_item.id
      : (Object.values(data.items).find(i => i.parent === null) || {}).id || null
  }
}
</script>
<style lang="scss">
</style>
