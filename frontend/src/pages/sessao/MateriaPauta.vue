<template>
  <div :class="['materia-pauta']">
    <div class="epigrafe">
      {{tipo_string}} n&#186; {{materia.numero}}/{{materia.ano}}
    </div>

    <div :class="['item-header', tipo_string ? '': 'd-none']">

      <div class="link-file">
        <a :href="materia.texto_original" class="btn btn-link">
          <i class="far fa-2x fa-file-pdf"></i>
        </a>
      </div>

      <div class="data-header">

        <div class="detail-header">
          <div class="protocolo-data" >
            <span>Protocolo: <strong>{{materia.numero_protocolo}}</strong></span>
            <span>{{data_apresentacao}}</span>
          </div>
          <div class="autoria" >
            <span v-for="(autores, key) in autores_list" :key="`al${key}`">{{autores.nome}}</span>
          </div>
        </div>

        <div class="ementa">
          {{materia.ementa}}
        </div>

      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'materia-pauta',
  props: ['materia'],
  data () {
    return {
      app: ['materia'],
      model: ['materialegislativa', 'tramitacao', 'anexada', 'autoria'],
      autores: {},
      tipo_string: ''
    }
  },
  watch: {
    materia: function (nv) {
      const t = this
      t.refresh()
    }
  },
  computed: {
    data_apresentacao () {
      try {
        const data = this.stringToDate(this.materia.data_apresentacao, 'yyyy-mm-dd', '-')
        return `${data.getDate()}/${data.getMonth() + 1}/${data.getFullYear()}`
      } catch (Exception) {
        return ''
      }
    },
    autores_list: {
      get () {
        return _.orderBy(this.autores, 'nome')
      }
    }
  },
  mounted () {
    const t = this
    setTimeout(() => {
      t.refresh()
    }, 2000)
  },
  methods: {
    fetch () {
    },
    refresh () {
      const t = this

      if (t.materia === undefined) {
        return
      }

      t.getObject({
        app: 'materia',
        model: 'tipomaterialegislativa',
        id: t.materia.tipo
      })
        .then(obj => {
          t.tipo_string = obj.descricao
        })

      t.$set(t, 'autores', {})

      t.$nextTick()
        .then(() => {
          _.each(t.materia.autores, (value) => {
            t.getObject({
              app: 'base',
              model: 'autor',
              id: value
            }).then(obj => {
              t.$set(t.autores, obj.id, obj)
            })
          })
        })
    }

  }
}
</script>

<style lang="scss">
.materia-pauta {
  .epigrafe {
    color: #044079;
    font-size: 125%;
    font-weight: bold;
    letter-spacing: 0.5px;
  }
  .ementa {
    margin: 0 0 0.5em 0;
    font-size: 135%;
    line-height: 1.4;
    color: #257464;
    text-align: left;
  }
  .item-header {
    display: grid;
    grid-template-columns: minmax(0, 50px) auto;
    align-items: center;
    grid-column-gap: 1em;
  }

  .detail-header {
    display: flex;
    font-size: 95%;
    align-items: center;
    flex-flow: row nowrap;

    .protocolo-data {
      flex: 0 0 auto;
      padding: 0.3em 0.5em 0.3em 0;
      span {
        display: inline-block;
        line-height: 2;
        border-right: 1px solid #00000055;
        padding-right: 0.5em;
        padding-left: 0.5em;
      }
      span:first-child {
        color: #800;
        padding-left: 0;
      }
    }
    .autoria {
      font-weight: bold;
      letter-spacing: 0.1px;
      line-height: 1.5;
      font-size: 95%;
      padding: 0.4em 0;
      span {
        display: inline-block;
        white-space: nowrap;
        &:after{
          content:";";
          padding-right: 0.5em;
        }
      }
      span:last-child:after {
        content:"";
      }
    }
  }
}

@media screen and (max-width: 480px) {

}
</style>
