<template>
  <div>
    <b-form-select v-model="selected" :options="options"/>
  </div>
</template>

<script>

export default {
  name: 'model-select',
  props: ['app', 'model', 'label', 'limit', 'ordering', 'choice'],
  data () {
    return {

      selected: null,
      options: [
        { value: null, text: this.label }
      ]
    }
  },
  watch: {
    selected: function (nv, ov) {
      this.$emit('change', nv)
    }
  },
  methods: {
    fetch (data) {
      this.fetchModel()
    },
    fetchModel (next_page = 1) {
      /**
       * Busca lista completa do model
       *   /api/[app]/[model]/
       *
       */
      let _this = this
      _this.options = [
        { value: null, text: this.label }
      ]
      _this.utils.getModelOrderedList(_this.app, _this.model, _this.ordering, next_page)
        .then((response) => {
          _.each(response.data.results, function (item, idx) {
            _this.options.push({ value: item.id, text: item[_this.choice] })
            _this.refreshState({
              app: _this.app,
              model: _this.model,
              value: item,
              id: item.id
            })
          })
          if (response.data.pagination.next_page !== null) {
            _this.fetchModel(response.data.pagination.next_page)
          }
        })
        .catch((response) => _this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 }))
    }
  },
  created: function () {
    this.fetchModel()
  }
}
</script>

<style lang="scss">

</style>
