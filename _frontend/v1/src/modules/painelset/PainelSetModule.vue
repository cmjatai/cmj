<template>
  <div class="painelset-module">
    <router-view></router-view>
  </div>
</template>

<script>

export default {
  name: 'painelset-module',
  data () {
    return {
    }
  },

  mounted: function () {
    try {
      this.$connect()
    } catch (e) {
      console.log(e) // Logs the error
    }
  },
  methods: {
  }
}
</script>

<style lang="scss">
</style>
