<template>
  <div class="pauta-online">
    <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
        Não existem Itens na Ordem do Dia com seus critérios de busca!
    </div>
    <div class="empty-list" v-if="!init">
        Carregando listagem...
    </div>

    <div class="item-expediente" v-if="itens.expedientesessao_list.length > 0">
      <div v-html="expediente(1)" class="inner">
      </div>
    </div>

    <div class="container-expedientemateria">

      <div v-if="itensDoExpediente.length" class="titulo-container">Matérias do Grande Expediente</div>
      <div class="inner">
        <item-de-pauta v-for="item in itensDoExpediente" :key="item.id" :item="item" type="expedientemateria"></item-de-pauta>
      </div>
    </div>

    <div class="item-expediente" v-if="itens.expedientesessao_list.length > 0">
      <div v-html="expediente(3)" class="inner">
      </div>
    </div>

    <div class="container-ordemdia">
      <div v-if="itensDaOrdemDia.length" class="titulo-container">Matérias da Ordem do Dia</div>
      <div class="inner">
        <item-de-pauta v-for="item in itensDaOrdemDia" :key="item.id * (-1)" :item="item" type="ordemdia"></item-de-pauta>
      </div>
    </div>
    <div class="item-expediente" v-if="itens.expedientesessao_list.length > 0">
      <div v-html="expediente(4)" class="inner">
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
        expedientesessao_list: [],
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
    setTimeout(() => {
      this.fetchItens()
      this.fetchExpedienteSessao()
    }, 1000)
  },
  methods: {
    expediente (tipo) {
      const esl = this.itens.expedientesessao_list
      let filtro = _.filter(esl, ['tipo', tipo])
      return filtro.length > 0 ? filtro[0].conteudo : ''
    },
    fetch (metadata) {
      if (metadata.action === 'post_delete') {
        this.$delete(this.itens[`${metadata.model}_list`], metadata.id)
        return
      }

      const t = this
      t.getObject(metadata)
        .then(obj => {
          t.$set(t.itens[`${metadata.model}_list`], metadata.id, obj)
        })

      /* t.utils.getModel(data.app, data.model, data.id)
        .then(response => {
          t.$set(t.itens[`${data.model}_list`], data.id, response.data)
        }) */
    },
    fetchItens (model_list = this.model) {
      const t = this
      _.mapKeys(model_list, function (value, key) {
        _.mapKeys(t.itens[`${value}_list`], function (obj, k) {
          obj.vue_validate = false
        })
        t.$nextTick()
          .then(function () {
            t.fetchList(1, value)
          })
      })
    },
    fetchExpedienteSessao () {
      const t = this
      return t.utils
        .getByMetadata({
          action: 'expedientes',
          app: 'sessao',
          model: 'sessaoplenaria',
          id: t.sessao.id
        })
        .then(response => {
          t.$set(t.itens, 'expedientesessao_list', response.data.results)
        })
        .then(obj => {
          // t.tramitacao.status = obj
        })
    },
    fetchList (page = null, model = null) {
      const t = this

      let query_string = `&sessao_plenaria=${this.sessao.id}`

      t.utils.getModelOrderedList('sessao', model, 'numero_ordem', page === null ? 1 : page, query_string)
        .then((response) => {
          t.init = true
          _.each(response.data.results, (value, idx) => {
            value.vue_validate = true
            if (value.id in t.itens[`${model}_list`]) {
              t.itens[`${model}_list`][value.id] = value
            } else {
              t.$set(t.itens[`${model}_list`], value.id, value)
            }
          })
          t.$nextTick()
            .then(function () {
              if (response.data.pagination.next_page !== null) {
                t.fetchList(response.data.pagination.next_page, model)
              } else {
                _.mapKeys(t.itens[`${model}_list`], function (obj, k) {
                  if (!obj.vue_validate) {
                    t.$delete(t.itens[`${model}_list`], obj.id)
                  }
                })
              }
            })
        })
        .catch((response) => {
          t.init = true
          t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a Ordem do Dia.', time: 5 })
        })
    }
  }
}
</script>

<style lang="scss">
.pauta-online {
  padding: 0 1em 1em;
  .titulo-container {
    color: #4e3c15;
    font-size: 200%;
    padding: 0.5em 0.5em 0.3em;
  }
  .container-expedientemateria {
    .titulo-container {
      color: #4e3c15;
    }
  }
  .container-ordemdia {
    .titulo-container {
      color: #0055ff;
    }
  }
  .item-expediente {
    .inner {
      background-color: white;
      padding: 1em;
      line-height: 1.2;
    }
  }
}

@media screen and (max-width: 767px) {
  .pauta-online {
    .titulo-container {
      font-size: 170%;
    }
  }
}

@media screen and (max-width: 480px) {
  .pauta-online {
    padding: 0;
    .titulo-container {
      font-size: 160%;
    }
  }
}

</style>
