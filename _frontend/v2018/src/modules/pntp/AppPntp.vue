<template>
  <div class="app-pntp container mt-5">
    <slot></slot>
    <div class="row">
      <div class="col-4">
        <app-menu-pntp v-bind:items="ptnp_data.items" v-bind:active_item="ptnp_data.active_item"></app-menu-pntp>
      </div>
      <div class="col-8"></div>
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
      ptnp_data: null
    }
  },
  mounted () {
    // le na página o <script id="pntp-data" type="application/json">
    let t = this
    let data = JSON.parse(document.getElementById('pntp-data').textContent)
    t.ptnp_data = data
  }
}
</script>
<style lang="scss">
</style>
