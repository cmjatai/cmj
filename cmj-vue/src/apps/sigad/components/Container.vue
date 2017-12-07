<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento)]">


    <div class="btn-toolbar widgets widget-top">
      <template v-if="childsOrdenados.length === 0">
        <div class="btn-group btn-group-xs pull-left">
          <button v-on:click.self="addChild(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-default" title="Adiciona Elemento no final deste Container...">{{tipo.text}}</button>
        </div>
      </template>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Container" type="button" class="btn btn-danger">x</button>
      </div>
    </div>


    <div class="btn-toolbar widgets widget-bottom ">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click="containerTrocarTipo" title="Trocar tipo deste Container" type="button" class="btn btn-default"><span class="glyphicon glyphicon-transfer" aria-hidden="true"></span></button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="addBrother('container', $event)" title="Adicionar novo Container Simples abaixo deste" type="button" class="btn btn-default">+C</button>
        <button v-on:click.self="addBrother('container-fluid', $event)" title="Adicionar novo Container Fluido abaixo deste"  type="button" class="btn btn-default">+CF</button>
      </div>
    </div>
    <div class="path-title-container construct">
      <input v-model.lazy="elemento.titulo" placeholder="Sub título do container..."/>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'

export default {
  name: 'container',
  extends: {
    ...DocumentoEdit,
  },
  methods: {
    addBrother(tipo, event) {
      let data = Object()
      data.tipo = this.getChoices.all_bycomponent[tipo].id
      data.parent = this.parent.id
      data.ordem = this.elemento.ordem + 1
      this.createBrother(data)
    },
    addChild(tipo, event) {
      let data = Object()
      data.tipo = this.getChoices.all_bycomponent[tipo].id
      data.parent = this.elemento.id
      this.createChild(data)
    },
    deleteParte(event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then( (response) => {
          t.$parent.getDocumento(this.parent.id)
          t.success('Elemento excluído com sucesso.')
        })
        .catch( (response) => {
          t.danger(response.response.data.detail)
        })
    },
    containerTrocarTipo(event) {
      let data = Object()
      let keys = _.keys(this.getChoices.tipo.containers)
      data.tipo = this.elemento.tipo === parseInt(keys[0]) ? keys[1] : keys[0]
      data.id = this.elemento.id
      this.updateDocumento(data)
    }
  },


}
</script>

<style lang="scss">
.container-fluid.container-documento-edit  {
  width: 98%;
  margin: 0 auto;
}
.container-documento-edit:not(.container-path){
  position: relative;
  margin-bottom: 10px;
  transition: all 0.5s ease;
  &:not(.container), &:not(.container-fluid) {
    .btn-danger {
      border-radius: 50%;
      width: 24px;
      height: 24px;
      display: inline-block;
      padding: 0;
      margin: 0;
      line-height: 20px;
      text-align: center;
    }
  }
  & > .widgets {
    opacity: 0;
    height: 0;
    display: none;
    position: absolute;
    z-index: 1;
    margin-top: -15px;
    width: 100%;
    transition: all 0.5s ease;
  }
  .widget-bottom {
    top:100%;
    right:-10px;
  }
  .widget-top {
    top: 0px;
    right:-10px;
  }
  &:hover {
    background: transparentize(#fff, 0.1);
    transition: all 0.5s ease;
    & > .widgets {
      display: block;
      height: auto;
      opacity: 0.6;
      transition: all 0.5s ease;
      &:hover {
        opacity: 1;
        transition: opacity 0.5s ease;
      }
    }
  }
}
</style>
