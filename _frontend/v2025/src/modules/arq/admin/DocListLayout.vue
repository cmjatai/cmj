<template>
  <div class="doclist-layout container-fluid" v-if="classe">
    <bread-crumb-classe :parents="classe.parents"></bread-crumb-classe>
    <div class="row-fluid">
      <div class="col">
        <h2>{{ classe.titulo }}</h2>
        <small v-html="descricao_html"></small>
        <div class="inner-list">
          <arq-doc-item :arqdoc="doc" :classe="classe" v-for="doc, k in arqdocs_ordered" :key="`ad-${k}`">
            {{ doc.titulo }}
          </arq-doc-item>
        </div>
        <div class="text-info">TODO: implementar paginação</div>
      </div>
      <div class="col-3 d-none">
        <div class="classechild">
          <h4>
            Subclasses de {{ classe.titulo }}
          </h4>
          {{ params_node }} - {{ params_nodechild }}
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import ArqDocItem from './ArqDocItem.vue'
import BreadCrumbClasse from './BreadCrumbClasse.vue'

export default {
  name: 'doc-list-layout',
  components: { ArqDocItem, BreadCrumbClasse },
  data () {
    return {
      params_node: this.$route.params.node,
      params_nodechild: this.$route.params.nodechild,
      classe: null,
      node_key_localstorage: 'portalcmj_arqnode_tree_opened',
      arqdocs: {},
      ARQCLASSE_FISICA: 100,
      ARQCLASSE_LOGICA: 200
    }
  },
  mounted () {
    const t = this
    t.fetchClasse()
      .then((response) => {
        _.each(t.classe.parents, function (item, idx) {
          localStorage.addArrayOfIds(t.node_key_localstorage, item.id)
        })
        t.$emit('checkIsOpenedNodesTree')
        const field_classe = t.classe.perfil === t.ARQCLASSE_FISICA ? 'classe_estrutural' : 'classe_logica'
        t.fetch(1, `&get_all=True&${field_classe}=${t.classe.id}`)
      })
  },
  computed: {
    arqdocs_ordered: {
      get () {
        return _.orderBy(this.arqdocs, ['id'], ['desc'])
      }
    },
    descricao_html: function () {
      let descr = this.classe.descricao
      descr = descr.replace('\r\n', '<br>')
      descr = descr.replace('\n', '<br>')
      return descr
    }
  },
  methods: {
    fetch (page = 1, query_string = '') {
      const _this = this
      _this.$set(_this, 'arqdocs', {})

      return _this.utils.getModelOrderedList('arq', 'arqdoc', '-data', page, query_string)
        .then((response) => {
          _.each(response.data, function (item, idx) {
            _this.$set(_this.arqdocs, item.id, item)
          })
        })
        .catch((response) => _this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar os documentos...', time: 5 }))
    },

    fetchClasse () {
      const _this = this

      if (_this.params_nodechild === 'root') {
        return null
      }

      return _this.getObject({
        action: '',
        app: 'arq',
        model: 'arqclasse',
        id: _this.params_nodechild
      })
        .then((classe) => {
          _this.classe = classe
          return classe
        })
        .catch((response) => _this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar classe selecionada...', time: 5 }))
    }
  }
}
</script>
<style lang="scss">
.container-arqtree {
  .doclist-layout {
    position: sticky;
    top: 0;
    z-index: 1;
    .inner-list {
      border: 1px solid #eee;
      margin: 15px 0;
      background-color: white;
    }
  }
  .row, .col-3 {
    position: relative;
  }
  .col-3 {
    border-left: 1px solid #ccc;
  }
  .classechild {
    position: sticky;
    display: block;
    top: 0;
  }
}
</style>
