<template>
  <div class="action-details" @mouseleave="mouseLeave">
    <div class="container-fluid">
      <div class="container d-flex">
        <div class="col col-auto">
          <slot name="subaction"></slot>
        </div>
        <div class="col flex-column" v-show="details && app !==''">
          <h3>{{titulo}}</h3>
          <component :is="`action-link-${link.model}`"
            v-for="(link, key) in linksArray"
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
import ActionLinkSessaoplenaria from './ActionLinkSessaoplenaria'
export default {
  name: 'action-details',
  components: {
    ActionLinkMaterialegislativa,
    ActionLinkDocumentoadministrativo,
    ActionLinkSessaoplenaria
  },
  data () {
    return {
      ro: null,
      details: false,
      links: [],
      app: '',
      model: '',
      params: '',
      titulo: ''
    }
  },
  computed: {
    linksArray: function () {
      return this.links
    },
    showAction: function () {
      let t = this
      return function (link) {
        return link.app === t.app && link.model === t.model && link.params === t.params
      }
    }
  },
  watch: {
    details: function (nv, od) {
      if (nv) {
        this.$emit('statictoggle', true)
      } else {
        this.$emit('statictoggle', false)
      }
    }
  },
  methods: {
    mouseLeave: function (event) {
      let _t = this
      let el = _t.$el
      el.firstElementChild.scrollTo(0, 0)

      if (_t.links.length === 0) {
        return
      }

      _t.app = _t.links[0].app
      _t.model = _t.links[0].model
      _t.params = _t.links[0].params
      _t.titulo = _t.links[0].titulo
    },
    mouseEnterLink: function (event) {
      let _t = this
      let app = event.target.getAttribute('app')

      if (app == null || app === '') {
        // _t.app = ''
        return
      }
      _t.titulo = event.target.text
      _t.app = app
      _t.model = event.target.getAttribute('model')
      _t.params = event.target.getAttribute('params')
    },
    loadLinks: function () {
      let _t = this
      let el = _t.$el
      let links = el.querySelectorAll('a')

      links.forEach(link => {
        link.addEventListener('mouseenter', this.mouseEnterLink)

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
          _t.titulo = link.text
        }

        _t.links.push({
          app: app,
          model: model,
          params: params,
          titulo: link.text

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
