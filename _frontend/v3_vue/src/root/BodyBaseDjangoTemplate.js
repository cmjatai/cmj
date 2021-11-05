
import RootRoute from './RootRoute.vue'

export default {
  components: {
    RootRoute
  },
  data () {
    return {
      var_teste: 'Teste de variável'
    }
  },
  methods: {
    teste () {
      console.log('teste body actions')
    }
  },
  mounted: function () {
    this.teste()
  }
}
