<template>
  <div class="sessaoplenaria-list">

    <form-sessao-list
      :pagination="pagination"
      v-on:nextPage="nextPage"
      v-on:previousPage="previousPage"
      v-on:currentPage="currentPage"
      v-on:changeFilter="changeFilter">
    </form-sessao-list>

    <div class="inner-list">
      <sessao-plenaria-item-list :sessao="item" v-for="(item, key) in sessoes" :key="key"></sessao-plenaria-item-list>
      <div class="empty-list" v-if="sessoes.length === 0 && init">
          Não foram encontradas Sessões Plenárias com seus critérios de busca!
      </div>
      <div class="empty-list" v-if="!init">
          Carregando listagem...
      </div>
    </div>
  </div>
</template>

<script>
import Resources from '@/resources'
import FormSessaoList from './FormSessaoList'
import SessaoPlenariaItemList from './SessaoPlenariaItemList'
export default {
  name: 'sessao-list',
  components: {
    FormSessaoList,
    SessaoPlenariaItemList
  },
  data () {
    return {
      utils: Resources.Utils,
      init: false,

      /**
       * monitora mudanças nestes models
       */
      app: ['sessao'],
      model: ['sessaoplenaria', 'tiposessaoplenaria'],

      ordering: '-data_inicio, -hora_inicio, -id',
      sessoes: [],
      pagination: {},
      form_filter: {
        year: null,
        month: null,
        tipo: null
      }
    }
  },
  methods: {
    currentPage (value) {
      this.fetch(value)
    },
    nextPage () {
      return this.pagination.next_page !== null ? this.fetch(this.pagination.next_page) : null
    },
    previousPage () {
      return this.pagination.previous_page !== null ? this.fetch(this.pagination.previous_page) : null
    },
    changeFilter (form_filter) {
      this.form_filter = form_filter
      this.fetch(1)
    },
    fetch (page = null) {
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
            _this
              .fetch(_this.pagination.previous_page)
              .catch(() => {
                _this.init = true
                _this.sendMessage(
                  { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 })
              })
          }
        })
    }
  },
  created: function () {
    let _this = this
    _this.fetch(1)
  }
}
</script>

<style lang="scss">
.sessaoplenaria-list {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: auto auto;
  grid-row-gap: 15px;
  .inner-list {
    display: grid;
    grid-template-columns: 1fr;
    //grid-row-gap: 1px;
  }
}

</style>
