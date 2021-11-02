import Push from './Push.vue'
export default {
  components: {
    Push
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
