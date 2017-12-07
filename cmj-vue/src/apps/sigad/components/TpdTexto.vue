<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento)]">
    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Fragmento de Texto" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-left">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-default" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>
    <span class="path-title-partes">
      <input v-model.lazy="elemento.titulo" placeholder="Título de Texto..."/>
    </span>
    <div class="construct">
      <textarea-autosize v-model.lazy="elemento.texto" placeholder="Fragmento de Texto..." :align="'text-left'"/>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import Container from './Container'

export default {
  name: 'tpd-texto',
  extends: {
    ...Container,
  },
  methods: {
  },
}
</script>

<style lang="scss">
.container-documento-edit {
  & > .tpd-texto {
    position: relative;
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
    &:hover {
    }
    input {
      font-weight: bold;
    }
    .widgets {
    margin-top: -15px;
    }
  }
}
</style>
