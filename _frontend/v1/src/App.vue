<template>
  <div id="app">
    <router-view></router-view>
    <message></message>
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
  }
}
</script>

<style lang="scss">

</style>
