<template>
  <div class="pauta-online">
    <div class="inner-list">
      <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
          Não existem Itens na Ordem do Dia com seus critérios de busca!
      </div>
      <div class="empty-list" v-if="!init">
          Carregando listagem...
      </div>

      <div v-for="(item, key) in itensOrdenados" :key="key+1">{{item.numero_ordem}}</div>

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
        ordemdia_list: {}
      },

      init: false,

      app: ['sessao'],
      model: ['expedientemateria', 'ordemdia']
    }
  },
  computed: {
    itensOrdenados: {
      get () {
        let itens = this.itens.ordemdia_list
        return _.orderBy(itens,'numero_ordem') // eslint-disable-line
      }
    }
  },
  mounted () {
    this.fetchOrdemDiaList(1)
  },
  methods: {
    fetch (data) {
      // this.itens.ordemdia_list = {}
      this.$set(this.itens, 'ordemdia_list', {})
      this.fetchOrdemDiaList(1)
    },
    fetchOrdemDiaList (page = null) {
      let _this = this

      let query_string = `&sessao_plenaria=${this.sessao.id}`

      _this.utils.getModelOrderedList('sessao', 'ordemdia', 'numero_ordem', page === null ? 1 : page, query_string)
        .then((response) => {
          _this.init = true
          _.each(response.data.results, (value, idx) => {
            _this.$set(_this.itens.ordemdia_list, value.id, value)
          })
          _this.$nextTick()
            .then(function () {
              // _this.itens.ordemdia_list = [..._this.itens.ordemdia_list, ...response.data.results]
              if (response.data.pagination.next_page !== null) {
                _this.fetchOrdemDiaList(response.data.pagination.next_page)
              }
            })
        })
        .catch((response) => {
          _this.init = true
          _this.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a Ordem do Dia.', time: 5 })
        })
    }
  }
}
</script>

<style lang="scss">

</style>
