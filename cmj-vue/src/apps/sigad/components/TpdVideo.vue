<template lang="html">
  <div :class="[classChild(elemento)]">
    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover este Vídeo" type="button" class="btn btn-danger">x</button>
      </div>
      <div v-show="elemento.texto" class="btn-group btn-group-xs pull-right">
        <button  v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Subtítulo para este Vídeo" type="button" class="btn btn-success">T</button>
        <button  v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para o Vídeo" type="button" class="btn btn-success">D</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-primary" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>

    <div class="inner">
      <span v-if="has_titulo || elemento.titulo" v-show="elemento.texto" class="path-title-partes"><input v-model.lazy="elemento.titulo" placeholder="Título do Vídeo..."/></span>
      <input v-if="has_descricao || elemento.descricao" v-show="elemento.texto" v-model.lazy="elemento.descricao" placeholder="Descrição do Vídeo..."/>

      <input v-model.lazy="elemento.texto" class="path-code" placeholder="Código de incorporação de Vídeo..."/>
      <div v-if="elemento.texto" class="embed-responsive embed-responsive-16by9">
        <span v-html="srcIframe"></span>
      </div>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import Container from './Container'

export default {
  name: 'tpd-video',
  extends: {
    ...Container,
  },
  computed: {
    srcIframe: function() {
        let iframe = this.elemento.texto
        iframe = iframe.replace('<iframe ', '<iframe class="embed-responsive-item" ' )
        return iframe
      }
  },
  methods: {},
}
</script>

<style lang="scss">
.container-documento-edit {
  .tpd-video, .tpd-audio {
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
