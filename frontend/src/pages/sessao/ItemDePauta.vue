<template>
  <div :class="['item-de-pauta', type]">
    <div class="empty-list" v-if="materia.id === undefined">
        Carregando Matéria...
    </div>
    <div class="item-header" v-if="tipo_string">
      <div class="data-header">
        <div class="epigrafe">
          {{tipo_string}} n&#186; {{materia.numero}}/{{materia.ano}}
        </div>
        <div class="detail-header">
          <div class="protocolo-data" >
            <span>Protocolo: <strong>{{materia.numero_protocolo}}</strong></span>
            <span>{{data_apresentacao}}</span>
          </div>
          <div class="autoria" >
            <div v-for="(autores_line, key) in autores_string" :key="`al${key}`">
              <span v-for="(autores, k) in autores_line" :key="`a${k}`">{{autores}}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="func-header">
        <a :href="materia.texto_original" class="btn btn-link">
          <i class="far fa-file-pdf"></i>
        </a>
      </div>
    </div>

    <div class="item-body">
      <div class="ementa">
        <a href=""></a>
        {{materia.ementa}}
      </div>
    </div>
    <div :class="['item-body', tipo_string && materia.anexadas.length > 0 ? 'col-anexadas':'']">
      <div class="col-1-body">

        <div class="ultima_tramitacao" v-if="nivel_detalhe >= NIVEL2 && tramitacao.ultima !== {}" >
          <strong>Situação:</strong> {{tramitacao.status.descricao}}<br>
          <strong>Ultima Ação:</strong> {{tramitacao.ultima.texto}}
        </div>
        <div v-if="nivel_detalhe >= NIVEL4 && observacao.length > 0" class="observacao" v-html="observacao"></div>
      </div>
      <div class="col-2-body">
      </div>
    </div>

  </div>
</template>
<script>
export default {
  name: 'item-de-pauta',
  props: ['item', 'type'],
  data () {
    return {
      app: ['materia'],
      model: ['materialegislativa', 'tramitacao'],
      materia: {},
      tramitacao: {
        ultima: {},
        status: {}
      },
      tipo_string: '',
      autores_string: [[]]
    }
  },
  watch: {
    materia: function (nv) {
      const t = this
      t
        .getObject({
          app: 'materia',
          model: 'tipomaterialegislativa',
          id: nv.tipo
        })
        .then(obj => {
          t.tipo_string = obj.descricao
        })

      t.autores_string = [[]]
      t.$nextTick()
        .then(() => {
          _.each(nv.autores, (value) => {
            t.getObject({
              app: 'base',
              model: 'autor',
              id: value
            }).then(obj => {
              if (t.autores_string[t.autores_string.length - 1].length < 5) {
                t.autores_string[t.autores_string.length - 1].push(obj.nome)
              } else {
                t.autores_string.push([])
                t.autores_string[t.autores_string.length - 1].push(obj.nome)
              }
            })
          })
        })
    }
  },
  computed: {
    data_apresentacao () {
      const data = this.stringToDate(this.materia.data_apresentacao, 'yyyy-mm-dd', '-')
      return `${data.getDate()}/${data.getMonth()}/${data.getFullYear()}`
    },
    observacao () {
      let o = this.item.observacao
      o = o.replace(/^\r\n/g, '')
      o = o.replace(/\r\n/g, '<br />')
      o = o.replace(/\r/g, ' ')
      o = o.replace(/\n/g, '<br />')
      return o
    }
  },
  mounted () {
    const t = this
    this
      .fetchMateria()
      .then((obj) => {
        t.fetchUltimaTramitacao()
      })
  },
  methods: {
    fetch (metadata = null) {
      if (metadata === null || metadata === undefined) {
        return
      }
      if (metadata.app === 'materia' && metadata.model === 'materialegislativa') {
        this.fetchMateria(metadata)
      } else if (metadata.app === 'materia' && metadata.model === 'tramitacao') {
        this.fetchUltimaTramitacao(metadata)
      }
    },
    fetchMateria (metadata) {
      const t = this
      return t
        .getObject({
          action: '',
          app: t.app[0],
          model: t.model[0],
          id: t.item.materia
        })
        .then(obj => {
          t.materia = obj
          return obj
        })
    },
    fetchUltimaTramitacao () {
      const t = this
      return t.utils
        .getByMetadata({
          action: 'ultima_tramitacao',
          app: 'materia',
          model: 'materialegislativa',
          id: t.materia.id
        })
        .then((response) => {
          t.tramitacao.ultima = response.data
          t.getObject({
            action: '',
            app: 'materia',
            model: 'statustramitacao',
            id: t.tramitacao.ultima.status
          })
            .then(obj => {
              t.tramitacao.status = obj
            })
        })
    }
  }
}
</script>

<style lang="scss">
.item-de-pauta {
  position: relative;
  background-color: #ffffff55;
  padding: 1em;
  //padding-bottom: 60px;
  margin-bottom: 1em;

  border-top: 1px solid #aaa;

  &:hover {
    background-color: #d6e6fd;
  }

  &::before {
    content: 'Ordem do Dia';
    position: absolute;
    bottom: 5px;
    right: 5px;
    color: rgba(#000, 0.1);
    font-size: 200%;
    display: inline-block;
    line-height: 1;
  }

  &.expedientemateria {
    &:hover {
      background-color: #ffbf00;
    }
    &::before {
      content: 'Grande Expediente';
    }
  }
  .item-header {
    display: grid;
    grid-template-columns: auto auto;

    .epigrafe {
      color: #044079;
      font-size: 125%;
      font-weight: bold;
      letter-spacing: 0.5px;
    }
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
      div:last-child {
        span:last-child:after {
          content:"";
        }
      }
    }
  }
  .func-header {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
  }
  .item-body {
    display: grid;

    &.col-anexadas {
      grid-template-columns: 2fr 1fr;
    }
    //

    .ementa {
      margin: 0.3em 0 0.5em 0;
      font-size: 135%;
      line-height: 1.4;
      color: #257464;
      text-align: left;
    }
    .observacao {
      display: inline-block;
      border-top: 1px solid #5696ca;
      margin: 0.5em 1em 0 0;
      padding-top: 0.5em;
      line-height: 1.3;
    }
    .ultima_tramitacao {
      border-top: 1px solid #5696ca;
      padding-top: 0.5em;
      line-height: 1.3;
    }
  }

}

@media screen and (max-width: 480px) {
  .item-de-pauta {
    font-size: 85%;
    .item-header {
      .epigrafe {
        letter-spacing: 0px;
      }
    }
  }
}
</style>
