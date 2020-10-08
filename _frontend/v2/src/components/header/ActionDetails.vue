<template>
  <div class="action-details">
    <div class="container d-flex">
      <div class="col col-auto">
        <slot name="subaction"></slot>
      </div>
      <div class="col" v-show="details">
        teste
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
      details: false
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
  },
  mounted: function () {
    let b = document.getElementsByTagName('body')[0]
    let _t = this

    this.ro = new ResizeObserver(entries => {
      _t.details = entries[0].target.offsetWidth >= 992
      console.log(entries[0].target.offsetWidth)
    })

    this.ro.observe(b)
  }
}
</script>

<style>

</style>
