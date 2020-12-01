
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
    handleTouch (event) {
      let ct = event.currentTarget

      if (event.type === 'touchstart') {
        ct.setAttribute('touchstart', event.changedTouches[0].screenX)
      } else {
        let x_inicial = ct.getAttribute('touchstart')

        if (x_inicial - event.changedTouches[0].screenX > 20) {
          let clickEvent = new CustomEvent('click')
          ct.children[1].dispatchEvent(clickEvent)
        } else if (x_inicial - event.changedTouches[0].screenX < -20) {
          let clickEvent = new CustomEvent('click')
          ct.children[0].dispatchEvent(clickEvent)
        }
      }
    },
    handleClickContainerScrollX (event) {
      let innerScroll = event.target.nextElementSibling

      let direction = 1
      if (innerScroll.classList.contains('btn-action-right')) {
        innerScroll = innerScroll.nextElementSibling
        direction = -1
      }

      let offsetWidth = (innerScroll.firstChild.offsetWidth + 23) * 3 * direction

      if (innerScroll.style.transform === '') {
        innerScroll.setAttribute('translate', 0)
      }

      let newTranslate = innerScroll.getAttribute('translate') - offsetWidth
      if (newTranslate < 0 && newTranslate * (-1) + offsetWidth / 3 < innerScroll.scrollWidth) {
        innerScroll.style.transform = `translateX(${newTranslate}px)`
        innerScroll.setAttribute('translate', newTranslate)

        innerScroll.previousElementSibling.previousElementSibling.style = 'display: flex'
      } else {
        innerScroll.setAttribute('translate', '')
        innerScroll.style.transform = `translateX(0px)`
        innerScroll.previousElementSibling.previousElementSibling.style = 'display: none'
      }
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
