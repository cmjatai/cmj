<template>
  <div id="app">
    <router-view></router-view>
    <slot />
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
  mounted: function () {
    this.loginStatus()
  }
}
</script>

<style lang="scss">

</style>
