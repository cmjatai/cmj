
<script>
import { mapActions } from 'vuex'
import BAlert from 'bootstrap-vue/es/components/alert/alert'
export default {
  name: 'alert',
  extends: {
    ...BAlert
  },
  props: [
    'message_id', 'show'
  ],
  data () {
    return {

    }
  },
  watch: {
    show: function (nv, ov) {
      if (nv <= 1) {
        this.popMessage(this.message_id)
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
