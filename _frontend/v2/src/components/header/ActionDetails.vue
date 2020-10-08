<template>
  <div class="action-details" @mouseleave="mouseLeave">
    <div class="container-fluid">
      <div class="container d-flex">
        <div class="col col-auto">
          <slot name="subaction"></slot>
        </div>
        <div class="col" v-show="details">
          teste<br>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
export default {
  name: 'action-details',
  data () {
    return {
      ro: null,
      details: false,
      links: []
    }
  },
  watch: {
    details: (nv, od) => {
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

    let links = el.querySelectorAll('a:not([app=""])')

    links.forEach(link => {
      _t.links.push({
        app: link.getAttribute('app'),
        model: link.getAttribute('model'),
        params: link.getAttribute('params'),
        values: []
      })
    })
  }
}
</script>

<style>

</style>
