<template>
  <div>
  </div>
</template>
<script>
export default {
  name: 'action-link',
  props: ['app', 'model', 'params'],
  data () {
    return {
      values: []
    }
  },
  methods: {
    fetch: function (app, model, params, page = 1) {
      const t = this
      t.utils
        .getModelList(app, model, page, `&${params}`)
        .then((response) => {
          this.values = response.data.results
        })
        .catch((response) => {
          t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a lista.', time: 5 })
        })
    }
  },
  mounted: function () {
    this.fetch(this.app, this.model, this.params)
  }
}
</script>
