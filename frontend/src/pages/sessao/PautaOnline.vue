<template>
  <div class="pauta-online">
    <div class="inner-list">
      <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
          Não existem Itens na Ordem do Dia com seus critérios de busca!
      </div>
      <div class="empty-list" v-if="!init">
          Carregando listagem...
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'pauta-online',
  props: ['sessao'],
  data () {
    return {
      itens: {
        ordemdia_list: []
      },
      init: false,

      app: ['sessao'],
      model: ['ordemdia']

    }
  },
  actions: {
    fetch (data) {
      this.fetchOrdemDiaList(1)
    },
    fetchSessaoList (page = null) {
      let _this = this

      if (page === null) {
        page = _this.pagination.page
      }

      let query_string = ''
      let ff = this.form_filter
      if (ff.year !== null) query_string += `&year=${ff.year}`
      if (ff.month !== null) query_string += `&month=${ff.month}`
      if (ff.tipo !== null) query_string += `&tipo=${ff.tipo}`

      return _this.utils.getModelOrderedList(_this.app[0], _this.model[0], _this.ordering, page === null ? 1 : page, query_string)
        .then((response) => {
          _this.init = true
          _this.sessoes = []
          _this.$nextTick()
            .then(function () {
              _this.sessoes = response.data.results
              _this.pagination = response.data.pagination
            })
        })
        .catch((response) => {
          if (page !== 1) {
            return _this
              .fetchSessaoList(1)
              .catch(() => {
                _this.init = true
                _this.sendMessage(
                  { alert: 'danger', message: 'Não foi possível recuperar a lista de Sessões.', time: 5 })
              })
          }
        })
    }

  }

}
</script>

<style lang="scss">

</style>
