<template lang="html">
  <div class="container-messages">
    <div :class="['alert', msg.alert]" v-for="(msg, key) in messages" :key="key">
      {{msg.message}}
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
export default {
  props: {
    messages: {
      type: Array,
      default () {
        return []
      }
    }
  },
  data () {
    return {
    }
  },
  computed: {},
  mounted () {},
  methods: {
    ...mapActions([
      'popMessage'
    ])
  },
  components: {}
}
</script>

<style lang="scss">
.container-messages {
  position: fixed;
  bottom: 20px;
  right: 0px;
  z-index: 100000;
}
</style>
