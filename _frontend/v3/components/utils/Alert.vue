<template>
  <div>
    <v-alert dismissible :type="message.alert" :value="visible">
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
    }, t.message.time * 1000 || 3000)
  },

  methods: {
    ...mapActions({
      popMessage: 'messages/popMessage',
    }),
  },
}
</script>

<style lang="scss" scoped>
</style>
