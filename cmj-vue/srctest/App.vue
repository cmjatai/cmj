
<template>
  <div id="app">
    <router-view class="view"></router-view>
  </div>
</template>

<script>

  import { mapGetters } from 'vuex'

  export default {
    name: 'app',
    data() {
      return {
      }
    },
    computed: {},
    methods: {}
  };
</script>


<style lang="scss">
  @import "./scss/app.scss"
</style>
