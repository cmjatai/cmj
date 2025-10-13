<template lang="html">
  <div :class="name_component">
    <div class="btn-toolbar widgets widget-top justify-content-end">
      <div v-if="!elemento.titulo" class="btn-group btn-group-sm">
        <button v-on:click.self="toogleTitulo" title="Disponibilizar Subtítulo para este Fragmento de Texto" type="button" class="btn btn-success">T</button>
      </div>
      <div class="btn-group btn-group-sm">
        <button v-on:click.self="toogleEditor" :title="[usartinymce ? 'Usar Editor Simples' : 'Usar Editor Avançado' ]" type="button" class="btn btn-success">Edição de Texto</button>
        <button v-on:click.self="deleteParte" title="Remover este Fragmento de Texto" type="button" class="btn btn-danger">x</button>
      </div>
    </div>

    <span v-if="has_titulo || elemento.titulo" class="path-title-partes">
      <input v-model.lazy="elemento.titulo" placeholder="Subtítulo para Fragmento de Texto..."/>
    </span>

    <div class="construct" v-if="usartinymce" >
      <editor v-if="usartinymce" inline  v-model.lazy="elemento.texto"
        :init="{
          plugins: 'lists',
          toolbar: 'undo redo | styles | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | indent outdent | bullist numlist',
          }">
      </editor>
    </div>

    <textarea-autosize  v-if="!usartinymce" v-model.lazy="elemento.texto" placeholder="Fragmento de Texto" :align="'text-left'"/>
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

import Editor from '@tinymce/tinymce-vue'
import 'tinymce/themes/silver/theme'

export default {
  name: 'tpd-texto',
  extends: {
    ...Container
  },
  components: {
    Editor
  },
  data () {
    return {
      usartinymce: true
    }
  },
  methods: {
    toogleEditor: function () {
      this.usartinymce = !this.usartinymce
    },

    success (message = 'Informação atualizada com sucesso.') {
      // this.sendMessage({ alert: 'alert-success', message: message })
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
