<template>
  <div :class="['item-de-pauta', type]">

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
        <div class="btn-toolbar" role="toolbar">
          <div class="btn-group ml-2 btn-group-sm" role="group" aria-label="First group">
            <a class="btn btn-outline-dark" @click="diminuirFonte">a</a>
            <a class="btn btn-outline-dark" @click="aumentarFonte">A</a>
          </div>
        </div>
      </div>
    </div>

    <div class="item-body">
      <div class="ementa">
        {{materia.ementa}}
      </div>
      <div class="observacao" v-html="observacao" v-if="observacao.length > 0"></div>
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
    this.fetchMateria()
  },
  methods: {
    diminuirFonte () {
      $('.base-layout').css('font-size', '-=1')
    },
    aumentarFonte () {
      $('.base-layout').css('font-size', '+=1')
    },
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
      t
        .getObject({
          action: '',
          app: t.app[0],
          model: t.model[0],
          id: t.item.materia
        })
        .then(obj => {
          t.materia = obj
        })
    },
    fetchUltimaTramitacao (metadata) {

    }
  }
}
</script>

<style lang="scss">
.item-de-pauta {
  user-select: none;
  position: relative;
  background-color: #ffffff55;
  padding: 10px;
  padding-bottom: 60px;
  margin-bottom: 15px;

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
    //border-top: 1px solid #ffbf00;
    //background-color: #e6e6a8;
    &:hover {
      background-color: #ffbf00;
      //border-top: 4px solid #beb9a9;
      //border-bottom: 4px solid #beb9a9;
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
      padding: 5px 10px 5px 0;
      span {
        display: inline-block;
        line-height: 2.3;
        border-right: 1px solid #00000055;
        padding-right: 10px;
        padding-left: 10px;
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
      padding: 5px 0;
      span {
        display: inline-block;
        white-space: nowrap;
        &:after{
          content:";";
          padding-right: 10px;
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
    align-items: start;
    a {
      padding: 10px 15px 7px;
      background-image: linear-gradient(to bottom, #fff, #e0e0e0);
      line-height: 1;
    }
  }
  .item-body {
    padding-right: 10px;
    .ementa {
      margin: 5px 0 15px 0;
      font-size: 135%;
      line-height: 1.4;
      color: #257464;
      text-align: left;
    }
    .observacao {
      display: inline-block;
      border-top: 1px solid rgb(86, 150, 202);
      padding: 5px 10px 0 0;
      line-height: 1.3;
    }
  }

}

@media screen and (max-width: 480px) {
  .item-de-pauta {
    //margin-bottom: 5px;
    padding: 5px 5px 5px 5px;
    border-left-width: 1px;
    border-radius: 0px;
  }
}
</style>
