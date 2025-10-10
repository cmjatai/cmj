<template>
  <div id="app">
    <router-view></router-view>
    <message></message>
  </div>
</template>

<script>
import Message from '@/components/utils/message/Message'
import Vuex from 'vuex'
export default {
  name: 'app',
  components: {
    Message
  },
  created: function () {
    this.loginStatus()
  },
  mounted: function () {
    this.initWebSocket()
  },
  methods: {
    ...Vuex.mapActions('store__sync', [
      'initWebSocket'
    ])
  }
}
</script>

<style lang="scss">

</style>
