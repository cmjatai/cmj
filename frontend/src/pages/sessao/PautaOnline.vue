<template>
  <div class="pauta-online">
    <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
        Não existem Itens na Ordem do Dia com seus critérios de busca!
    </div>
    <div class="empty-list" v-if="!init">
        Carregando listagem...
    </div>

    <div class="container-expedientemateria">
      <div v-if="itensDoExpediente.length" class="titulo-container">Matérias do Grande Expediente</div>
      <div class="inner">
        <item-de-pauta v-for="item in itensDoExpediente" :key="item.id" :item="item" type="expedientemateria"></item-de-pauta>
      </div>
    </div>

    <div class="container-ordemdia">
      <div v-if="itensDaOrdemDia.length" class="titulo-container">Matérias da Ordem do Dia</div>
      <div class="inner">
        <item-de-pauta v-for="item in itensDaOrdemDia" :key="item.id * (-1)" :item="item" type="ordemdia"></item-de-pauta>
      </div>
    </div>

  </div>
</template>

<script>
import ItemDePauta from './ItemDePauta'
export default {
  name: 'pauta-online',
  props: ['sessao'],
  components: {
    ItemDePauta
  },
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
    fetch (metadata) {
      if (metadata.action === 'post_delete') {
        this.$delete(this.itens[`${metadata.model}_list`], metadata.id)
        return
      }

      const _this = this
      _this.getObject(metadata)
        .then(obj => {
          _this.$set(_this.itens[`${metadata.model}_list`], metadata.id, obj)
        })

      /* _this.utils.getModel(data.app, data.model, data.id)
        .then(response => {
          _this.$set(_this.itens[`${data.model}_list`], data.id, response.data)
        }) */
    },
    fetchItens (model_list = this.model) {
      const _this = this
      _.mapKeys(model_list, function (value, key) {
        _.mapKeys(_this.itens[`${value}_list`], function (obj, k) {
          obj.vue_validate = false
        })
        _this.$nextTick()
          .then(function () {
            _this.fetchList(1, value)
          })
      })
    },
    fetchList (page = null, model = null) {
      const _this = this

      let query_string = `&sessao_plenaria=${this.sessao.id}`

      _this.utils.getModelOrderedList('sessao', model, 'numero_ordem', page === null ? 1 : page, query_string)
        .then((response) => {
          _this.init = true
          _.each(response.data.results, (value, idx) => {
            value.vue_validate = true
            if (value.id in _this.itens[`${model}_list`]) {
              _this.itens[`${model}_list`][value.id] = value
            } else {
              _this.$set(_this.itens[`${model}_list`], value.id, value)
            }
          })
          _this.$nextTick()
            .then(function () {
              if (response.data.pagination.next_page !== null) {
                _this.fetchList(response.data.pagination.next_page, model)
              } else {
                _.mapKeys(_this.itens[`${model}_list`], function (obj, k) {
                  if (!obj.vue_validate) {
                    _this.$delete(_this.itens[`${model}_list`], obj.id)
                  }
                })
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
@import "~@/scss/variables";

.pauta-online {
  padding: 0 $padding-space $padding-space;
  .titulo-container {
    color: #4e3c15;
    font-size: 200%;
    padding: 30px 10px 20px 15px;
  }
}

@media screen and (max-width: 991px) {
  .pauta-online {
    .titulo-container {
      padding: 20px 10px 15px 15px;
    }
  }
}

@media screen and (max-width: 767px) {
  .pauta-online {
    padding: 0;
    .titulo-container {
      font-size: 130%;
    }
  }
}

</style>
