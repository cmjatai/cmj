<template>
  <div :class="['item-de-pauta', type]">
    <div class="item-header" v-if="tipo_string">
      <div class="titulo">
        {{tipo_string}} n&#186; {{materia.numero}}/{{materia.ano}}
      </div>
      <span>Protocolo: {{materia.numero_protocolo}}</span>
    </div>
    <div class="item-body">
    {{materia.ementa}}
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
      tipo_string: ''
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
    }
  },
  mounted () {
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
  methods: {
    fetch (metadata) {

    }
  }

}
</script>
<style lang="scss">
.item-de-pauta {
  position: relative;
  background-image: url("~@/assets/img/bg.png");
  background-color: white;
  padding: 10px 15px;
  margin-bottom: 15px;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  font-size: 1.5rem;
  line-height: 2rem;
  &:hover {
    background-color: #dbdbdb;
    border-top: 4px solid #d0d0d0;
    border-bottom: 4px solid #d0d0d0;
    border-radius: 4px;
  }

  &::before {
    content: 'Ordem do Dia';
    position: absolute;
    bottom: 5px;
    right: 5px;
    color: rgba(#000, 0.03);
    font-size: 200%;
    line-height: 1rem;
  }

  &.expedientemateria {
    background-color: #e2dcca;
    background-image: none;
    &:hover {
      background-color: #ffbf00;
      border-top: 4px solid #beb9a9;
      border-bottom: 4px solid #beb9a9;
    }
    &::before {
      content: 'Grande Expediente';
    }
  }
  .item-header {
    padding-bottom: 10px;
    .titulo {
      font-weight: bold;
      color: #01776d;
    }
  }

  .item-body {
    color: #2e4c74;
  }
}

@media screen and (max-width: 991px) {
}
</style>
