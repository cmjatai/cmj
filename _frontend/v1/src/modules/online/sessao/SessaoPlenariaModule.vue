<template>
  <div class="sessaoplenaria-module">
    <router-view></router-view>
  </div>
</template>

<script>

export default {
  name: 'sessaoplenaria-module',
  data () {
    return {
      models_init_cache: {
        base: ['autor'],
        sessao: [
          'tiposessaoplenaria',
          {
            model: 'expedientesessao',
            full_pages: false,
            ordering: '-sessao_plenaria'
          }
        ],
        materia: ['tipomaterialegislativa', 'statustramitacao'],
        parlamentares: [
          'legislatura',
          {
            model: 'sessaolegislativa',
            full_pages: false,
            ordering: '-data_inicio'
          }
        ]
      }
    }
  },

  mounted: function () {
    try {
      this.$connect()
    } catch (e) {
      console.log(e) // Logs the error
    }
    this.initCache()
  },
  methods: {
    fetchList (page = null, _app = null, _model = null) {
      const t = this
      t.utils
        .getModelOrderedList(_app,
          t.isString(_model) ? _model : _model.model,
          t.isString(_model) ? '' : _model.ordering,
          page === null ? 1 : page
        )
        .then((response) => {
          _.each(response.data.results, (_value, idx) => {
            t.refreshState({
              app: _app,
              model: t.isString(_model) ? _model : _model.model,
              id: _value.id,
              value: _value
            })
          })
          t.$nextTick()
            .then(function () {
              if (response.data.pagination.next_page !== null) {
                if (t.isString(_model) || _model.full_pages) {
                  t.fetchList(response.data.pagination.next_page, _app, _model)
                }
              }
            })
        })
    },
    initCache () {
      const t = this
      _.mapKeys(t.models_init_cache, function (model_list, app) {
        _.each(model_list, function (model) {
          t.fetchList(1, app, model)
        })
      })
    }
  }
}
</script>

<style lang="scss">
</style>
