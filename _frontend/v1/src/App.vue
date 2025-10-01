<template>
  <div id="app">
    <message></message>
    <router-view></router-view>
  </div>
</template>

<script>
import Message from '@/components/utils/message/Message'
export default {
  name: 'app',
  components: {
    Message
  },
  created: function () {
    this.loginStatus()
  },
  mounted: function () {
  }
}
</script>

<style lang="scss">

</style>
