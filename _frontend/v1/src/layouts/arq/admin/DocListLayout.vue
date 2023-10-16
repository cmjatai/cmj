<template>
  <div class="doclist-layout p-2" v-if="classe">
    <nav aria-label="breadcrumb" v-if="classe.parents">
      <ol class="breadcrumb">
        <li class="breadcrumb-item" v-for="parent, k in classe.parents" :key="`cp-${k}`">
          <router-link :to="{ name: 'childroute', params: { node: params_node, nodechild: parent.id } }">{{ parent.titulo }}</router-link>
        </li>
      </ol>
    </nav>
    <h2>{{ classe.titulo }}</h2>
    <small v-html="descricao_html"></small>
    <br><br>
    {{ params_node }}<br>
    {{ params_nodechild }}
  </div>
</template>
<script>
export default {
  name: 'doc-list-layout',
  data () {
    return {
      params_node: this.$route.params.node,
      params_nodechild: this.$route.params.nodechild,
      classe: null
    }
  },
  mounted () {
    this.fetchClasse()
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
    fetchClasse () {
      const _this = this
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
  }
}
</style>
