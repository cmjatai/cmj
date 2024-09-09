<template>
  <div>
    <b-form-select v-model="selected" :options="options" :select-size="height"/>
  </div>
</template>

<script>

export default {
  name: 'model-select',
  props: ['value',
    'app', 'model',
    'label',
    'limit',
    'ordering',
    'choice', 'height', 'extra_query', 'required'
  ],
  data () {
    return {
      selected: this.value,
      options: []
    }
  },
  watch: {
    selected: function (nv, ov) {
      this.$emit('change', nv)
    },
    value: function (nv, ov) {
      this.selected = nv
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
      if (next_page === 1) {
        if (!_this.height || this.height === 1) {
          if (_this.required === undefined || !_this.required) {
            _this.selected = _this.value ? _this.value : null
            _this.options = [
              { value: _this.selected, text: this.label ? this.label : '---------------' }
            ]
          }
        }
      }

      let query_string = _this.isString(_this.extra_query) ? _this.extra_query : ''

      _this.utils.getModelOrderedList(_this.app, _this.model, _this.ordering, next_page, query_string)
        .then((response) => {
          _.each(response.data.results, function (item, idx) {
            _this.options.push({ value: item, text: item[_this.choice] })
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
