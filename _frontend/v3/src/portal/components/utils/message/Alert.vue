<template>
  <div class="alert">

  </div>
</template>
<script>
import { mapActions } from 'vuex'
export default {
  name: 'alert',
  props: [
    'messageId', 'show'
  ],
  data () {
    return {

    }
  },
  watch: {
    show: function (nv, ov) {
      if (nv <= 1) {
        this.popMessage(this.messageId)
      }
    }
  },

  methods: {
    ...mapActions([
      'popMessage'
    ])
  }

}
</script>

<style lang="scss" scoped>
</style>
