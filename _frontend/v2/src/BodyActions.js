
import App from './App'
export default {
  components: {
    App
  },
  data () {
    return {
      searching: ''
    }
  },
  methods: {
    teste () {
      // console.log('teste')
    },
    handleBlurSearch (event) {
      this.searching = ''
    },
    handleFocusSearch (event) {
      this.searching = 'd-searching'
    }
  }
}
