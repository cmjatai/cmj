<template>
  <div class="sessao-plenaria-online">
    <div v-if="sessao" >
      <sessao-plenaria-item-list :sessao="sessao"></sessao-plenaria-item-list>
      <ordem-dia-list :sessao="sessao"></ordem-dia-list>
    </div>
  </div>
</template>
<script>
import SessaoPlenariaItemList from './SessaoPlenariaItemList'
import OrdemDiaList from './OrdemDiaList'
export default {
  name: 'sessao-plenaria-online',
  components: {
    SessaoPlenariaItemList,
    OrdemDiaList
  },
  data () {
    return {
      sessao: null,
      app: ['sessao'],
      model: ['sessaoplenaria']
    }
  },
  mounted: function () {
    this.fetchSessao()
  },
  methods: {
    fetchSessao () {
      let _this = this
      let id = _this.$route.params.id

      let meta = {
        app: _this.app[0],
        model: _this.model[0],
        id: id
      }

      _this.getObject(meta)
        .then(obj => {
          _this.sessao = obj
        })
    },
    fetch (data) {
      /**
       * O Mixin global que escuta o websocket é que decide em chamar o fetch
       * baseado em [this.app] e [this.model]
       */

      this.fetchSessao()
      if (data.app === this.app[0] &&
          data.model === this.model[0] &&
          data.id === this.sessao.id) {
        this.fetchSessao()
      }
    }
  }

}
</script>

<style lang="scss">
  .sessao-plenaria-online {
    .sessao-plenaria-item-list {
      padding: 5px;
      .subtitulo {
        .separator {
          display: inline;
        }
      }
    }
  }
</style>
