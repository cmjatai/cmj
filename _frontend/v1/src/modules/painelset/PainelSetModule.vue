<template>
  <div class="painelset-module">
    <router-view></router-view>
  </div>
</template>

<script>
import Vuex from 'vuex'
export default {
  name: 'painelset-module',
  data () {
    return {
    }
  },
  mounted: function () {
    const t = this
    t.setSideleftVisivel(true)
    t.setSiderightVisivel(false)
    try {
      this.$connect()
    } catch (e) {
      console.log(e) // Logs the error
    }
  },
  methods: {
    ...Vuex.mapActions([
      'setSideleftVisivel',
      'setSiderightVisivel'
    ])
  }
}
</script>

<style lang="scss">
</style>
