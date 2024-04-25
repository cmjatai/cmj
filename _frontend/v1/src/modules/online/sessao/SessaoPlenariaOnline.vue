<template>
  <div class="sessao-plenaria-online" >
    <template v-if="sessao" >
      <sessao-plenaria-topo :sessao="sessao"></sessao-plenaria-topo>
      <pauta-online :sessao="sessao"></pauta-online>
    </template>
  </div>
</template>
<script>
import SessaoPlenariaTopo from './SessaoPlenariaTopo'
import PautaOnline from './PautaOnline'

export default {
  name: 'sessao-plenaria-online',
  components: {
    SessaoPlenariaTopo,
    PautaOnline
  },
  data () {
    return {
      sessao: null,
      idd: parseInt(this.$route.params.id),
      app: ['sessao'],
      model: ['sessaoplenaria']
    }
  },
  mounted () {
    let t = this
    t.$nextTick(() => {
      t
        .getObject({
          action: '',
          id: t.idd,
          app: t.app[0],
          model: t.model[0]
        })
        .then(value => {
          this.sessao = value
        })
        .catch(() => {
          this.sessao = (this.cache.sessao !== undefined &&
                    this.cache.sessao.sessaoplenaria !== undefined &&
                    this.cache.sessao.sessaoplenaria[this.idd] !== undefined) ? this.cache.sessao.sessaoplenaria[this.idd] : null
        })
    })
  },
  methods: {
    fetch (data) {
      let t = this
      if (data.id === this.idd &&
          data.app === this.app[0] &&
          data.model === this.model[0]) {
        if (data.action === 'post_delete') {
          setTimeout(() => {
            t.sendMessage(
              { alert: 'danger', message: 'Sessão Plenária foi excluída', time: 5 })

            t.$router.push({ name: 'sessao_list_link' })
          }, 500)
        } else {
          this.sessao = this.cache.sessao.sessaoplenaria[this.idd]
        }
      }
    }
  }

}
</script>

<style lang="scss">
  .sessao-plenaria-online {
    position: relative;
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
