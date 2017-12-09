<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento)]">
    <div class="btn-toolbar widgets widget-top">
      <div v-show="elemento.texto" class="btn-group btn-group-xs pull-left">
        <button  v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Título para o Áudio" type="button" class="btn btn-success">T</button>
        <button  v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para o Áudio" type="button" class="btn btn-success">D</button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Áudio" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-left">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-default" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>

    <div class="inner">
      <span v-if="has_titulo || elemento.titulo" v-show="elemento.texto" class="path-title-partes"><input v-model.lazy="elemento.titulo" placeholder="Título do Áudio..."/></span>
      <input v-if="has_descricao || elemento.descricao" v-show="elemento.texto" v-model.lazy="elemento.descricao" placeholder="Descrição do Áudio..."/>
      <input v-model.lazy="elemento.texto"  class="path-code" placeholder="Código de incorporação de Áudio..."/>
      <div v-if="elemento.texto" class="embed-responsive embed-responsive-16by9 embed-audio">
        <span v-html="srcIframe"></span>
      </div>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import TpdVideo from './TpdVideo'

export default {
  name: 'tpd-audio',
  extends: {
    ...TpdVideo,
  },
  computed: {},
  methods: {},
}
</script>

<style lang="scss">
.container-documento-edit {
  & > .tpd-audio {
    position: relative;
    .btn-danger {
      border-radius: 50%;
    }
    .widgets {
      margin-top: -7px;
    }
    input.path-code {
      font-size: 50%;
      font-family: monospace;
      background: transparentize(#fff, 0.2);
      color: #22f;
      &::-webkit-input-placeholder { /* Chrome/Opera/Safari */
        color: #55b;
      }
      &::-moz-placeholder { /* Firefox 19+ */
        color: #55b;
      }
      &:-ms-input-placeholder { /* IE 10+ */
        color: #55b;
      }
      &:-moz-placeholder { /* Firefox 18- */
        color: #55b;
      }
    }
  }
}
</style>
