<template>
  <div>
    <b-form-select v-model="selected" :options="options" :select-size="height" :disabled="disabled"/>
  </div>
</template>

<script>

export default {
  name: 'model-select',
  props: ['value',
    'app', 'model', 'action',
    'label',
    'limit',
    'ordering',
    'choice', 'height', 'extra_query', 'required', 'disabled'

  ],
  data () {
    return {
      selected: this.value,
      options3: []
    }
  },
  computed: {
    options: function () {
      let cache = _.orderBy(Object.values(
        this.data_cache[`${this.app}_${this.model}`] || []
      ), [this.ordering], ['asc'])
      return _.filter([
        !this.required ? { value: null, text: '----------------' } : null,
        ...cache.map((item) => {
          return {
            value: item,
            text: item[this.choice]
          }
        })
      ], (item) => item !== null)
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
  mounted: function () {
    const _this = this
    _this.fetchSync({
      app: _this.app,
      model: _this.model,
      action: _this.action,
      query_string: _this.extra_query ? _this.extra_query : ''
    })
  }

}
</script>

<style lang="scss">

</style>
