<template>
  <div id="app">
    <message v-bind:messages="getMessages"></message>
    <router-view>

    </router-view>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
export default {
  name: 'app',
  data () {
    return {
    }
  },
  computed: {
    ...mapGetters({
      getMessages: 'getMessages'
    })
  }
}
</script>

<style lang="scss">
  @import "../scss/app.scss";
</style>
