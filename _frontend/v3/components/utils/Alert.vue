<template>
  <div>
    <v-alert
      dense
      dismissible
      min-width="25vw"
      :type="message.alert"
      :value="visible"
    >
      {{ message.message }}
    </v-alert>
  </div>
</template>
<script>
import { mapActions } from 'vuex'
/*
watch: {
    show: function (nv, ov) {
      if (nv <= 1) {
        this.popMessage(this.messageId)
      }
    },
  },
*/
export default {
  name: 'Alert',
  props: {
    message: {
      type: Object,
      require: true,
      default: () => {},
    },
  },
  data() {
    return {
      visible: true,
    }
  },
  mounted() {
    const t = this
    setTimeout(() => {
      t.popMessage(t.message)
      t.visible = false
    }, t.message.timeout * 1000 || 3000)
  },

  methods: {
    ...mapActions({
      popMessage: 'utils/messages/popMessage',
    }),
  },
}
</script>

<style lang="scss" scoped>
@media screen and (max-width: 958.98px) {
  .v-alert {
    margin-bottom: 0.5rem;
  }
}
@media screen and (min-width: 960px) {
  .v-alert {
    max-width: 50vw;
  }
}
</style>
