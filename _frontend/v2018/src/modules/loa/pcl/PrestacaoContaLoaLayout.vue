<template>
  <div class="prestacaocontaloa-layout">
  </div>
</template>

<script>
export default {
  name: 'prestacaocontaloa-layout',
  data () {
    return {
      loa: { id: this.$route.params.pkloa }
    }
  },
  methods: {
  },
  mounted: function () {
    const t = this
    t.removeAside()
    t.$nextTick()
      .then(() => {
        t.utils.fetch({
          app: 'loa',
          model: 'loa',
          id: t.loa.id,
          params: {
            expand: 'parlamentares'
          }
        })
          .then((response) => {
            t.loa = response.data
            // t.fetch()
          })
      })
  }
}
</script>
