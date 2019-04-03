<template>
  <router-link :class="'sessao-plenaria-item-list'" :to="{ name: 'sessao_plenaria_online_link', params: {id: sessao.id} }">
    <h3 class="tit">
      {{titulo}}
    </h3>
    <div class="subtitulo">
      <span>{{subtitulo}}</span><span class="separator"> – </span><span>{{date_text}}</span>
    </div>
  </router-link>
</template>

<script>
import { mapState } from 'vuex'
export default {
  name: 'sessao-plenaria-item-list',
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
    ...mapState({
      cache: state => state.cache
    }),
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
      let meta_list = _.clone(t.metadata)

      _.mapKeys(meta_list, function (value, key) {
        let meta = meta_list[key]
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
.sessao-plenaria-item-list {
  display: grid;
  grid-template-columns: auto auto;
  align-items: center;
  background-image: url("~@/assets/img/bg.png");
  border-bottom: 1px solid #ccc;
  padding: 1em;
  line-height: 1;
  grid-column-gap: 0.5em;
  cursor: pointer;

  &:first-child {
    border-top: 1px solid #ccc;
  }

  &:hover {
    background-color: rgba($color: #f5f5f5, $alpha: 0.9);
    text-decoration: none;
  }
  .subtitulo {
    color: #777;
    display: inline-block;
    text-align: right;
    line-height: 1.2;
    .separator {
      display: block;
      height: 0px;
      overflow: hidden;
    }
  }
  h3 {
    line-height: 1;
    color: #553d14;
    margin-bottom: 0px;
  }
}
@media screen and (max-width: 1199px) {
  .sessao-plenaria-item-list {
    grid-template-columns: auto;
    line-height: 1.3;
    h3 {
      font-size: 110%;
    }
    .subtitulo {
      line-height: 1;
      text-align: left;
    }
  }
}
@media screen and (max-width: 600px) {
  .sessao-plenaria-item-list {
    h3 {
      font-size: 100%;
    }
    .subtitulo {
    }
  }
}
@media screen and (max-width: 480px) {
  .sessao-plenaria-item-list {
    padding: 0.5em;
    h3 {
      font-size: 85%;
    }
    .subtitulo {
      font-size: 75%;
    }
  }
}
</style>
