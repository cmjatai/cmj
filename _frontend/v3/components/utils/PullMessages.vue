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
      getMessages: 'utils/messages/getMessages',
    }),
  },
}
</script>

<style lang="scss">
.pull-messages {
  position: fixed;
  z-index: 99999;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: flex-end;

  bottom: 0px;
  right: 0.5rem;
  margin-left: 0.5rem;
}
@media screen and (max-width: 958.98px) {
}
@media screen and (min-width: 960px) {
  .pull-messages {
    right: 1rem;
    margin-left: 1rem;

    opacity: 0.75;
    &:hover {
      opacity: 1;
      &:not(:empty) {
        padding-top: 10%;
      }
    }
  }
}
</style>
