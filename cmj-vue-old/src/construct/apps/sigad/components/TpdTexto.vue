<template lang="html">
  <div :class="name_component">
    <div class="btn-toolbar widgets widget-top justify-content-end">
      <div v-if="!elemento.titulo" class="btn-group btn-group-sm">
        <button v-on:click.self="toogleTitulo" title="Disponibilizar Subtítulo para este Fragmento de Texto" type="button" class="btn btn-success">T</button>
      </div>
      <div class="btn-group btn-group-sm">
        <button v-on:click.self="toogleEditor" :title="[usarfroala ? 'Usar Editor Simples' : 'Usar Editor Avançado' ]" type="button" class="btn btn-success">Edição de Texto</button>
        <button v-on:click.self="deleteParte" title="Remover este Fragmento de Texto" type="button" class="btn btn-danger">x</button>
      </div>
    </div>

    <span v-if="has_titulo || elemento.titulo" class="path-title-partes">
      <input v-model.lazy="elemento.titulo" placeholder="Subtítulo para Fragmento de Texto..."/>
    </span>
    <div class="construct" v-if="usarfroala" >
      <froala v-if="usarfroala" :tag="'textarea'" :config="config" v-model.lazy="elemento.texto"></froala>
    </div>

    <textarea-autosize  v-if="!usarfroala" v-model.lazy="elemento.texto" placeholder="Fragmento de Texto" :align="'text-left'"/>
    <component :is="classChild(value)" v-for="value in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
    <div class="btn-toolbar widgets widget-bottom justify-content-end">
      <div class="btn-group btn-group-sm">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="(tipo, key) in getChoices.tipo.subtipos" :key="key" type="button" class="btn btn-primary" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>
  </div>
</template>

<script>
import Container from './Container'

export default {
  name: 'tpd-texto',
  extends: {
    ...Container
  },
  data () {
    return {
      config: {
        toolbarInline: true,
        toolbarButtons: ['bold', 'italic', 'underline', 'strikeThrough', 'subscript', 'superscript', 'align', 'formatOL', 'formatUL', 'indent', 'outdent', 'undo', 'redo'],
        quickInsertButtons: [],
        quickInsertTags: [],
        typingTimer: 1000,
        placeholderText: 'Fragmento de Texto... ',
        events: {
          'froalaEditor.initialized': function () {
          }
        }
      },
      model: 'texto do model',
      usarfroala: true
    }
  },
  methods: {
    toogleEditor: function () {
      this.usarfroala = !this.usarfroala
    }
  }
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
