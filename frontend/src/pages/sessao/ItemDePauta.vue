<template>
  <div :class="['item-de-pauta', type]">

    <div class="item-header" v-if="tipo_string">
      <div class="epigrafe">
        {{tipo_string}} n&#186; {{materia.numero}}/{{materia.ano}}
      </div>
      <div class="protocolo-data-autoria">
        <span>Protocolo: {{materia.numero_protocolo}}</span>
        <span>{{data_apresentacao}}</span>
        <span>{{autores_string.join(', ')}}</span>
      </div>
    </div>

    <div class="item-body">
      <div class="ementa">
        {{materia.ementa}}

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
      model: ['materialegislativa'],
      materia: {},
      tipo_string: '',
      autores_string: []
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

      t.autores_string = []
      t.$nextTick()
        .then(() => {
          _.each(nv.autores, (value) => {
            t.getObject({
              app: 'base',
              model: 'autor',
              id: value
            }).then(obj => {
              t.autores_string.push(obj.nome)
            })
          })
        })
    }
  },
  computed: {
    data_apresentacao () {
      const data = this.stringToDate(this.materia.data_apresentacao, 'yyyy-mm-dd', '-')
      return `${data.getDate()}/${data.getMonth()}/${data.getFullYear()}`
    }
  },
  mounted () {
    this.fetch()
  },
  methods: {
    fetch (metadata = null) {
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
    }
  }
}
</script>

<style lang="scss">
.item-de-pauta {
  position: relative;
  background-color: white;
  padding: 10px 15px 10px 10px;
  margin-bottom: 15px;
  font-size: 100%;
  line-height: 1;

  &::before {
    content: 'Ordem do Dia';
    position: absolute;
    bottom: 5px;
    right: 5px;
    color: rgba(#000, 0.05);
    font-size: 200%;
  }

  &.expedientemateria {
    background-color: #e6e6a8;
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
    .epigrafe {
      color: #044079;
      font-size: 125%;
      font-weight: bold;
      letter-spacing: 0.5px;
    }
    .protocolo-data-autoria {
      line-height: 2rem;
      span {
        padding: 0 10px;
        border-right: 1px solid #00000055;
      }
      span:first-child {
        color: #800;
        padding-left: 0;
      }
      span:last-child {
        padding-right: 0;
        border-right: 0px solid black;
        font-weight: bold;
        font-size: 95%;
      }
    }
  }
  .item-body {
    .ementa {
      margin: 10px 0;
      font-size: 150%;
      line-height: 1.4;
      color: rgb(37, 116, 100);
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
