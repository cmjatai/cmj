<template lang="html">
  <div class="container-messages">
    <alert
      :variant="msg.alert"
      show
      dismissible
      v-for="(msg, key) in getMessages"
      :key="key"
      v-model="msg.time"
      :messageId="msg.id">
        {{msg.message}}
    </alert>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Alert from './Alert'
export default {
  name: 'message',
  data () {
    return {
    }
  },
  computed: {
    ...mapGetters({
      getMessages: 'getMessages'
    })
  },
  components: {
    Alert
  }
}
</script>

<style lang="scss" scoped>
.container-messages {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  z-index: 10000;
}
</style>
