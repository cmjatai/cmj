<script>
import { mapActions } from 'vuex'
import { BAlert } from 'bootstrap-vue/esm/components/alert/alert'
export default {
  name: 'alert',
  extends: BAlert,
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
.alert-error {
  background-color: #f8d7da;
  color: #721c24;
  border-color: #f5c6cb;
}
.alert-warning {
  background-color: #fff3cd;
  color: #856404;
  border-color: #ffeeba;
}
.alert-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border-color: #bee5eb;
}
.alert-success {
  background-color: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}
</style>
