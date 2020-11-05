
export default {
  components: {
    App: () => import('./App'),
    ActionDetails: () => import('@/components/header/ActionDetails')
  },
  data () {
    return {
      searching: '',
      static: '',
      portalmenu_opened: false
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
    },
    handleClickPortalMenu (event) {
      this.portalmenu_opened = !this.portalmenu_opened
      // this.$cookie.set('portalmenu_opened', this.portalmenu_opened ? 'opened' : 'closed')
    },
    staticToggleAction (flag) {
      this.static = flag ? '' : ''
      // this.static = flag ? 'static' : ''
    }
  },
  mounted: function () {
    let portalmenu_opened = 'closed' // this.$cookie.get('portalmenu_opened')

    if (portalmenu_opened === null) {
      portalmenu_opened = false
    } else {
      portalmenu_opened = portalmenu_opened === 'opened'
    }
    this.portalmenu_opened = portalmenu_opened
  }

}
