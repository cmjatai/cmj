<template>
  <div :class="'sessao-plenaria-topo'" >
      <div class="tit">
        {{titulo}}
      </div>
      <div class="subtitulo">
        <span>{{subtitulo}}</span> – <span>{{date_text}}</span>
      </div>
  </div>
</template>

<script>
export default {
  name: 'sessao-plenaria-topo',
  props: ['sessao'],
  data () {
    return {
      app: ['sessao', 'parlamentares'],
      model: ['sessaoplenaria', 'sessaolegislativa', 'tiposessaoplenaria', 'legislatura'],

      data_inicio: new Date(),
      sessao_legislativa: { numero: '' },
      tipo: { nome: '' },
      legislatura: { numero: '' },

      metadata: {
        sessao_legislativa: { app: 'parlamentares', model: 'sessaolegislativa', id: this.sessao.sessao_legislativa },
        legislatura: { app: 'parlamentares', model: 'legislatura', id: this.sessao.legislatura },
        tipo: { app: 'sessao', model: 'tiposessaoplenaria', id: this.sessao.tipo }
      }
    }
  },
  watch: {
    sessao: function (nv) {
      this.updateSessao()
      this.fetch()
    }
  },
  computed: {
    titulo: function () {
      let sessao = this.sessao
      let tipo = this.tipo
      let data_inicio = this.data_inicio
      return `${sessao.numero}ª ${tipo.nome} da 
              ${data_inicio.getDate() > 15 ? 2 : 1}ª Quizena do Mês de 
              ${this.month_text(data_inicio.getMonth())} de 
              ${data_inicio.getFullYear()}
              `
    },
    subtitulo: function () {
      return `${this.sessao_legislativa.numero}ª Sessão Legislativa da 
              ${this.legislatura.numero}ª Legislatura`
    },
    date_text: function () {
      return `${this.data_inicio.getDate()} de 
              ${this.month_text(this.data_inicio.getMonth())} de
              ${this.data_inicio.getFullYear()} – ${this.sessao.hora_inicio}`
    }
  },
  methods: {
    fetch (metadata) {
      let t = this
      _.mapKeys(t.metadata, function (value, key) {
        let meta = t.metadata[key]
        t.getObject(meta)
          .then(obj => {
            t[key] = obj
          })
      })
    },
    updateSessao () {
      this.data_inicio = this.stringToDate(this.sessao.data_inicio, 'yyyy-mm-dd', '-')
      this.metadata.sessao_legislativa.id = this.sessao.sessao_legislativa
      this.metadata.tipo.id = this.sessao.tipo
      this.metadata.legislatura.id = this.sessao.legislatura
    }
  },
  mounted: function () {
    this.updateSessao()
    this.fetch()
  }

}
</script>
<style lang="scss">

.sessao-plenaria-topo {
  display: grid;
  grid-template-columns: auto auto;
  align-items: start;
  padding: 0 0.3em 1em 0.3em;
  line-height: 1;
  cursor: default;
  grid-column-gap: 10px;
  text-align: left;
  font-size: 95%;

  .tit {
    color: #493b23;
    margin-bottom: 0px;
  }
  .subtitulo {
    color: #777;
    text-align: right;
    font-size: 90%;
  }
}

@media screen and (max-width: 800px) {
  .sessao-plenaria-topo {
    grid-template-columns: auto;
    justify-content: center;
    text-align: center;
    .subtitulo {
      text-align: center;
    }
  }
}

@media screen and (max-width:480px) {
  .sessao-plenaria-topo {
    font-size: 82%;
  }
}

</style>
