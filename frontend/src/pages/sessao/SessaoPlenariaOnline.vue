<template>
  <div class="sessao-plenaria-online">
    <div  v-if="sessao" >
    <sessao-plenaria-item-list :sessao="sessao"></sessao-plenaria-item-list>
  teste
    </div>
  </div>
</template>
<script>
import SessaoPlenariaItemList from './SessaoPlenariaItemList'
import Resources from '@/resources'
export default {
  name: 'sessao-plenaria-online',
  components: {
    SessaoPlenariaItemList
  },
  data () {
    return {
      utils: Resources.Utils,
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

      let sessao = _this.getModel(meta)
      if (sessao === null || !sessao.hasOwnProperty(id)) {
        _this.$nextTick()
          .then(() => {
            _this
              .insertInState(meta)
              .then(() => {
                sessao = _this.getModel(meta)
                _this.sessao = sessao[id]
              })
          })
      } else {
        _this.sessao = sessao[id]
      }
    },
    fetch () {
      /**
       * O Mixin global que escuta o websocket é que decide em chamar o fetch
       * baseado em [this.app] e [this.model]
       */
      this.fetchSessao()
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
