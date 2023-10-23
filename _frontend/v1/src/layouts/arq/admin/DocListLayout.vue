<template>
  <div class="doclist-layout container-fluid" v-if="classe">
    <nav aria-label="breadcrumb" v-if="classe.parents">
      <ol class="breadcrumb">
        <li class="breadcrumb-item" v-for="parent, k in classe.parents" :key="`cp-${k}`">
          <router-link :to="{ name: 'arqchildroute', params: { node: k > 0 ? classe.parents[k-1].id : 'root', nodechild: parent.id } }"
            @click.native="clickItemBreadCrumb">
            {{ parent.titulo }}
          </router-link>
        </li>
      </ol>
    </nav>
    <div class="row-fluid">
      <div class="col">
        <h2>{{ classe.titulo }}</h2>
        <small v-html="descricao_html"></small>
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
export default {
  name: 'doc-list-layout',
  data () {
    return {
      params_node: this.$route.params.node,
      params_nodechild: this.$route.params.nodechild,
      classe: null,
      node_key_localstorage: 'portalcmj_arqnode_tree_opened'
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
      })
  },
  computed: {
    descricao_html: function () {
      let descr = this.classe.descricao
      descr = descr.replace('\r\n', '<br>')
      descr = descr.replace('\n', '<br>')
      return descr
    }
  },
  methods: {
    clickItemBreadCrumb () {
      this.$refs.noderoot.reload()
    },
    fetchClasse () {
      const _this = this

      if (_this.params_nodechild === 'root') {
        return null
      }

      return _this.utils.getModel('arq', 'arqclasse', _this.params_nodechild)
        .then((response) => {
          _this.classe = response.data
          return response
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
