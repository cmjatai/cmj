<template lang="html">
  <div class="pull-messages">
    <alert
      v-for="(msg, key) in getMessages"
      :key="`msg-${key}`"
      :message="msg">
    </alert>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Alert from './Alert'
export default {
  name: 'PullMessages',
  components: {
    alert: Alert,
  },
  data() {
    return {}
  },
  computed: {
    ...mapGetters({
      getMessages: 'messages/getMessages',
    }),
  },
}
</script>

<style lang="scss" scoped>
.pull-messages {
  position: fixed;
  bottom: 0px;
  right: 1rem;
  z-index: 99999;
}
</style>
