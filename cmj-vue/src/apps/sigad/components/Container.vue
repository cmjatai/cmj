<template lang="html">
  <div :class="classChild(elemento)">
    <div class="btn-toolbar widgets widget-topright ">
      <div class="btn-group btn-group-xs">
        <button v-on:click.self="deleteParte" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom ">
      <div class="btn-group btn-group-xs">
        <button v-on:click.self="addParte('container', $event)" type="button" class="btn btn-default">+C</button>
        <button v-on:click.self="addParte('container-fluid', $event)"  type="button" class="btn btn-default">+CF</button>
      </div>
    </div>
    <div class="path-subtitle construct">
      <input v-model.lazy="elemento.titulo" placeholder="Sub título do container..."/>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childs" :child="value" :parent="elemento" :key="value.id"/>
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
    addParte(tipo, event) {
      let data = Object()
      data.tipo = this.getChoices.all_bycomponent[tipo].id
      data.parent = this.parent.id
      data.ordem = this.elemento.ordem + 1
      this.createChild(data)
    },
    deleteParte(event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then( (response) => {
          t.$parent.getDocumento(this.parent.id)
          console.log(response.statusText)
        })
        .catch( (response) => {
          console.log(response.statusText)
        })
    },
    createChild(data) {
      let t = this
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.$parent.getDocumento(response.data.parent)
        })
        .catch( (response) => {
          console.log(response.statusText)
        })
    },
  }

}
</script>

<style lang="scss" scoped>
.container-fluid {
  width: 98%;
  margin: 0 auto;
}
.container, .container-fluid {
  position: relative;
  margin-bottom: 10px;
  .widgets {
    display: none;
    position: absolute;
    z-index: 1;
    margin-top: -10px;
  }
  .widget-bottom {
    top:100%;
  }
  .widget-topright {
    top: 0px;
    right:-10px;
  }
  &:hover {
    background: transparentize(#fff, 0.5);
    .widgets {
      display: block;
    }
  }
}
</style>
