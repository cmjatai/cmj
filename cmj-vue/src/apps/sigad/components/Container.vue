<template lang="html">
  <div :class="[classChild(elemento), childsOrdenados.length !== 0 ?  '': 'empty' ]">


    <div class="btn-toolbar widgets widget-top">
      <div  v-if="!elemento.titulo" class="btn-group btn-group-xs pull-left">
        <button v-on:click.self="toogleTitulo" title="Disponibilizar Título para o Container" type="button" class="btn btn-success">T</button>
      </div>
      <template v-if="childsOrdenados.length === 0">
        <div class="btn-group btn-group-xs pull-left">
          <button v-on:click.self="addChild(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-primary" title="Adiciona Elemento no final deste Container...">{{tipo.text}}</button>
        </div>
      </template>
      <div class="btn-group btn-group-xs pull-right">
      </div>
    </div>

    <div class="btn-toolbar widgets widget-bottom ">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Container" type="button" class="btn btn-danger">x</button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click="containerTrocarTipo" title="Trocar tipo deste Container" type="button" class="btn btn-default"><span class="glyphicon glyphicon-transfer" aria-hidden="true"></span></button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="addBrother('container', $event)" title="Adicionar novo Container Simples abaixo deste" type="button" class="btn btn-default">+C</button>
        <button v-on:click.self="addBrother('container-fluid', $event)" title="Adicionar novo Container Fluido abaixo deste"  type="button" class="btn btn-default">+CF</button>
      </div>
    </div>
    <div v-if="has_titulo || elemento.titulo" class="path-title-container construct">
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
  data() {
    return {
      has_titulo: false,
      has_descricao:false,
      has_autor: false,
    }
  },
  methods: {
    toogleTitulo(event) {
      this.has_titulo = !this.has_titulo
    },
    toogleDescricao(event) {
      this.has_descricao = !this.has_descricao
    },
    toogleAutor(event) {
      this.has_autor = !this.has_autor
    },
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
.container-documento-edit {
  .container-fluid  {
    width: 98%;
  }
  .container, .container-fluid {
    border: 1px solid transparent;
    position: relative;
    margin: 15px auto 30px;
    padding: 15px 0px 30px;
    background: transparentize(#bbb, 0.85);
    border: 1px solid #fafafa;
    border-radius: 5px;
    & > .widgets  {
      .btn {
        height: 30px;
      }
    }
    &.empty {
      padding: 30px;
        & > .widgets {
        display: block;
        height: auto;
        opacity: 0.4;
      }
    }
    &:hover {
      transition: all 0.5s ease;
      & > .widgets {
        transition: all 0.5s ease;
        display: block;
        height: auto;
        opacity: 0.7;
        &:hover {
          opacity: 1;
          transition: all 0.5s ease;
        }
      }
    }
  }
}
</style>
