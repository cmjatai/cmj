<template lang="html">
    <div :class="[name_component, 'path-imagem', alinhamento(elemento)]">
      <div class="btn-toolbar widgets widget-top justify-content-between">
        <div class="btn-group btn-group-sm">
          <button v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Título para a Imagem" type="button" class="btn btn-success">T</button>
          <button v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para a Imagem" type="button" class="btn btn-success">D</button>
          <button v-if="!elemento.autor" v-on:click.self="toogleAutor" title="Disponibilizar Autor para a Imagem" type="button" class="btn btn-success">A</button>
        </div>
        <div class="btn-group btn-group-sm">
          <button v-on:click="alinhar(key, $event)" v-for="(alinhamento, key) in getChoices.alinhamento" type="button" class="btn btn-primary" :title="alinhamento.text" v-html="icons[key]" :key="key"></button>
          <button v-on:click.self="deleteParte" title="Remover esta Imagem" type="button" class="btn btn-danger">x</button>
        </div>
      </div>

      <div class="inner">
        <drop-zone v-on:change="changeImage" :elemento="elemento" :src="slug" :multiple="false" :resource="documentoResource"/>
        <span v-if="has_titulo || elemento.titulo" class="path-title-partes">
          <input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/>
        </span>
        <input v-if="has_descricao || elemento.descricao" v-model.lazy="elemento.descricao" placeholder="Descrição da Imagem..."/>
        <input v-if="has_autor || elemento.autor" v-model.lazy="elemento.autor" placeholder="Autor da Imagem..."/>
      </div>
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
import { mapGetters } from 'vuex'

export default {
  name: 'tpd-image',
  extends: {
    ...Container
  },
  components: {
  },
  data () {
    return {
      icons: {
        0: '<i class="fa fa-align-left" aria-hidden="true"></i>',
        1: '<i class="fa fa-align-justify" aria-hidden="true"></i>',
        2: '<i class="fa fa-align-right" aria-hidden="true"></i>',
        3: '<i class="fa fa-align-center" aria-hidden="true"></i>'
      }
    }
  },
  computed: {
    ...mapGetters([
      'getChoices',
      'getDocObject'
    ])
  },
  methods: {
    changeImage: function () {
      this.getDocumento(this.elemento.id)
    },
    alinhamento: function (value) {
      let al = value.alinhamento
      try {
        return this.getChoices.alinhamento[al]['component_tag']
      } catch (Exception) {
        return ''
      }
    },
    alinhar (alinhamento, ev) {
      let data = Object()
      data.alinhamento = alinhamento
      data.id = this.elemento.id
      this.elemento.alinhamento = alinhamento
      this.updateDocumento(data)
    }
  }
}
</script>

<style lang="scss" scoped>
.container-documento-edit {
  .tpd-image {
    z-index: 3;
    margin-top: 13px ;
    &.alinhamento-justify {
      padding-top: 10px;
      padding-bottom: 10px;
      clear: left;
    }
    &.alinhamento-center{
      margin: 0 auto ;
    }
  }
}
</style>
