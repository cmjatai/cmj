<template>
  <div class="pauta-online">
    <div class="inner-list">
      <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
          Não existem Itens na Ordem do Dia com seus critérios de busca!
      </div>
      <div class="empty-list" v-if="!init">
          Carregando listagem...
      </div>

      <div v-for="item in itensDoExpediente" :key="item.id">{{item.numero_ordem}}</div>

      <div v-for="item in itensDaOrdemDia" :key="item.id">{{item.numero_ordem}}</div>

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
        ordemdia_list: {},
        expedientemateria_list: {}
      },

      init: false,

      app: ['sessao'],
      model: ['expedientemateria', 'ordemdia']
    }
  },
  computed: {

    itensDaOrdemDia: {
      get () {
        return _.orderBy(this.itens.ordemdia_list, 'numero_ordem')
      }
    },
    itensDoExpediente: {
      get () {
        return _.orderBy(this.itens.expedientemateria_list, 'numero_ordem')
      }
    }
  },
  mounted () {
    this.fetchItens()
  },
  methods: {
    fetch (data) {
      // this.itens.ordemdia_list = {}
      this.$set(this.itens, 'ordemdia_list', {})
      this.$set(this.itens, 'expedientemateria_list', {})
      this.fetchItens()
    },
    fetchItens () {
      let _this = this
      _.mapKeys(this.model, function (value, key) {
        _this.fetchList(1, value)
      })
    },
    fetchList (page = null, model = null) {
      let _this = this

      let query_string = `&sessao_plenaria=${this.sessao.id}`

      _this.utils.getModelOrderedList('sessao', model, 'numero_ordem', page === null ? 1 : page, query_string)
        .then((response) => {
          _this.init = true
          _.each(response.data.results, (value, idx) => {
            if (value.id in _this.itens[`${model}_list`]) {
              _this.itens[`${model}_list`][value.id] = value
            } else {
              _this.$set(_this.itens[`${model}_list`], value.id, value)
            }
          })
          _this.$nextTick()
            .then(function () {
              // _this.itens.ordemdia_list = [..._this.itens.ordemdia_list, ...response.data.results]
              if (response.data.pagination.next_page !== null) {
                _this.fetchList(response.data.pagination.next_page, model)
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
