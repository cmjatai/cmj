<template>
  <div class="action-details" @mouseleave="mouseLeave">
    <div class="container-fluid">
      <div class="container d-flex">
        <div class="col col-auto">
          <slot name="subaction"></slot>
        </div>
        <div class="col" v-show="details">
          <component :is="`action-link-${link.model}`"
            v-for="(link, key) in links"
            :key="key"
            :app="link.app"
            :model="link.model"
            :params="link.params"
            v-show="showAction(link)"></component>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import ActionLinkMaterialegislativa from './ActionLinkMaterialegislativa'
import ActionLinkDocumentoadministrativo from './ActionLinkDocumentoadministrativo'
export default {
  name: 'action-details',
  components: {
    ActionLinkMaterialegislativa,
    ActionLinkDocumentoadministrativo
  },
  data () {
    return {
      ro: null,
      details: false,
      links: [],
      app: '',
      model: '',
      params: ''

    }
  },
  computed: {
    showAction: function () {
      let t = this
      return function (link) {
        return link.app === t.app && link.model === t.model && link.params === t.params
      }
    }
  },
  watch: {
    details: function (nv, od) {
      let p = document.getElementById('portalactions')
      if (nv) {
        p.classList.add('static')
      } else {
        p.classList.remove('static')
      }
    }
  },
  methods: {
    mouseLeave: function (event) {
      let _t = this
      let el = _t.$el
      el.firstElementChild.scrollTo(0, 0)
    },
    mouseEnterLink: function (event) {
      console.log(event.target.getAttribute('model'), event.target)
    },
    loadLinks: function () {
      let _t = this
      let el = _t.$el
      let links = el.querySelectorAll('a')

      links.forEach(link => {
        let app = link.getAttribute('app')
        let model = link.getAttribute('model')
        let params = link.getAttribute('params')

        if (app == null || app === '') {
          return
        }

        if (_t.app === '') {
          _t.app = app
          _t.model = model
          _t.params = params
        }

        link.addEventListener('mouseenter', this.mouseEnterLink)

        _t.links.push({
          app: app,
          model: model,
          params: params
        })
      })
    }
  },
  mounted: function () {
    let h = document.getElementsByTagName('header')[0]
    let _t = this
    let el = _t.$el

    this.ro = new ResizeObserver(entries => {
      _t.details = entries[0].target.offsetWidth >= 992
      let rect = el.parentElement.getBoundingClientRect()
      el.style.setProperty('--leftvalue', `${rect.left + rect.width / 2 - 10}px`)
    })
    this.ro.observe(h)
    this.loadLinks()
  }
}
</script>

<style>

</style>
