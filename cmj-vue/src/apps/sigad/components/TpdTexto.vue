<template lang="html">
  <div :class="name_component">
    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Fragmento de Texto" type="button" class="btn btn-danger">x</button>
      </div>
      <div v-if="!elemento.titulo" class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="toogleTitulo" title="Disponibilizar Subtítulo para este Fragmento de Texto" type="button" class="btn btn-success">T</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-primary" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>
    <span v-if="has_titulo || elemento.titulo" class="path-title-partes">
      <input v-model.lazy="elemento.titulo" placeholder="Subtítulo para Fragmento de Texto..."/>
    </span>
    <div class="construct">
      <froala :tag="'textarea'" :config="config" v-model.lazy="elemento.texto"></froala>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import Container from './Container'
import VueFroala from 'vue-froala-wysiwyg'

export default {
  name: 'tpd-texto',
  extends: {
    ...Container,
  },
  data () {
    return {
      config: {
        toolbarInline: true,
        toolbarButtons: ['bold', 'italic', 'underline', 'strikeThrough', 'subscript', 'superscript',  'align', 'formatOL', 'formatUL', 'indent', 'outdent',  'undo', 'redo'],
        quickInsertButtons: [],
        quickInsertTags: [],
        typingTimer: 1000,
        placeholderText: 'Fragmento de Texto... ',
        events: {
          'froalaEditor.initialized': function () {
            console.log('initialized')
          }
        }
      },
      model: 'texto do model'
    }
  },
  methods: {
  },
}
</script>

<style lang="scss">
.container-documento-edit {
  .tpd-texto {
    padding-top: 15px;
    .path-title-partes {
      padding: 0;
      width: 45%;
      display: inline-block;
    }
  }
}
</style>
