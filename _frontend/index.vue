<template>
  <div class="max-w-screen-lg mx-auto max-w-screen-xl">
    ------------------<br />
    <br />
    {{ rserver.__str__ }} <br />
    {{ rserver.ementa }}
    ------------------<br />
    <br />
    {{ rclient.__str__ }} <br />
    {{ rclient.ementa }}
  </div>
</template>

<script>
export default {
  fetchOnServer: false,
  async asyncData({ params, $axios }) {
    const rserver = await $axios.$get('/materia/materialegislativa/18600/')
    return { rserver }
  },
  data() {
    return {
      rclient: {},
    }
  },
  async fetch() {
    this.rclient = await this.$axios.$get('/materia/materialegislativa/18500/')
  },
}
</script>
