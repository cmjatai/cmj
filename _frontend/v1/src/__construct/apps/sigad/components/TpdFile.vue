<template lang="html">
  <div :class="[name_component, 'draggable', classDrag, is_imagem ? 'images-list': 'files-list']"
    v-on:dragend="dragend"
    v-on:dragenter="dragenter"
    v-on:dragleave="dragleave"
    v-on:dragover="dragover"
    v-on:dragstart="dragstart"
    v-on:dragexit="dragexit"
    v-on:drop="drop"
    v-on:mouseover="mouseOver"
    v-on:mouseleave="mouseLeave">

      <div :class="[is_imagem ? 'image-render': 'file-render']">
        <img :src="slug+'.256?'+refresh" v-if="is_imagem">
      </div>

      <div v-if="!is_imagem" >
        <div class="path-title-file construct">
          <input v-model.lazy="elemento.titulo" placeholder="Título do Arquivo..."/>
        </div>
        <input v-model.lazy="elemento.autor" placeholder="Autor..."/>
        <div class="path-description-file construct">
          <textarea-autosize v-model.lazy="elemento.descricao" placeholder="Descrição do Documento"/>
        </div>
      </div>

      <div class="drop-area" v-if="!is_imagem">
        <drop-zone v-on:change="changeImage" :elemento="elemento" :src="''" :multiple="false" :resource="documentoResource"/>
      </div>
      <div class="btn-controls">

        <a :href="slug" target="_blank" v-if="!is_imagem" class="btn btn-link" >
          <i class="fas fa-file"></i>
        </a>
        <span v-if="is_imagem" class="btn btn-rotate"  v-on:click="rotateLeft" title="Rotacionar 90 graus a esquerda">
          <i class="fas fa-undo" aria-hidden="true"></i>
        </span>
        <span v-if="is_imagem" class="btn btn-rotate"  v-on:click="rotateRight" title="Rotacionar 90 graus a direita">
          <i class="fas fa-redo" aria-hidden="true"></i>
        </span>
        <span class="btn btn-delete"  v-on:click="deleteParte" >
          <i class="fas fa-trash" aria-hidden="true"></i>
        </span>
      </div>
      <div class="btn-toolbar widgets widget-bottom justify-content-end">
        <div class="btn-group btn-group-sm">
          <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="(tipo, key) in getChoices.tipo.subtipos" :key="key" type="button" class="btn btn-primary" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
        </div>
      </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import TpdImageTdBi from './TpdImageTdBi.vue'

export default {
  name: 'tpd-file',
  extends: {
    ...TpdImageTdBi
  },
  components: {
  },
  data () {
    return {
      TIPOS_IMG_PERMITIDOS: [
        'image/jpeg',
        'image/jpg',
        'image/jpe_',
        'image/pjpeg',
        'image/vnd.swiftview-jpeg',
        'application/jpg',
        'application/x-jpg',
        'image/pjpeg',
        'image/pipeg',
        'image/vnd.swiftview-jpeg',
        'image/x-xbitmap',
        'image/bmp',
        'image/x-bmp',
        'image/x-bitmap',
        'image/png',
        'application/png',
        'application/x-png'
      ],

      dragged: false,
      draggedover: 0,
      draggedleave: false,
      mouseover: false
    }
  },
  computed: {
    ...mapGetters([
      'getChoices',
      'getDocObject'
    ]),
    is_imagem: function () {
      return this.TIPOS_IMG_PERMITIDOS.indexOf(this.elemento.mime_type) !== -1
    },
    classDrag: function () {
      let classes = Array() //eslint-disable-line
      this.dragged ? classes.push('drag-start') : '' //eslint-disable-line
      this.draggedleave ? classes.push('drag-leave') : '' //eslint-disable-line
      this.draggedover !== 0 ? classes.push('drag-over') : '' //eslint-disable-line
      return classes
    }
  },
  methods: {
    changeImage: function () {
      this.getDocumento(this.elemento.id)
    },
    mouseOver (ev) {
      this.mouseover = true
    },
    mouseLeave (ev) {
      this.mouseover = false
    },
    dragend (ev) {
      console.log('dragend: TpdFile', ev)
      if (this.dragged) {
        this.$emit('ondragend', this.elemento)
      }
      this.dragged = false
      this.draggedleave = false
      this.draggedover = 0
    },
    dragenter (ev) {
      console.log('dragenter: TpdFile', ev)
      if (this.dragged) {
        this.draggedleave = false // não deve ser atribuido true em caso contrário
      }
    },
    dragleave (ev) {
      console.log('dragleave: TpdFile', ev)
      this.$emit('ondragleave', this.elemento, this.draggedover)
      this.draggedleave = this.dragged
      this.draggedover = 0
    },
    dragover (ev) {
      console.log('dragover: TpdFile', ev)
      if (!this.dragged) {
        this.draggedover = ev.offsetX - ev.target.offsetWidth / 2
      }
    },
    dragstart (ev) {
      console.log('dragstart: TpdFile', ev)
      this.dragged = true
    },
    dragexit (ev) {
      console.log('dragexit: TpdFile', ev)
    },
    drop (ev) {
      console.log('drop: TpdFile', ev)
    },
    rotateLeft: function () {
      let t = this
      let data = Object()
      data.id = t.elemento.id
      data.rotate = 90
      t.updateDocumento(data)
        .then(() => {
          t.elemento.refresh = _.now() // eslint-disable-line
        })
    },
    rotateRight: function () {
      let t = this
      let data = Object()
      data.id = t.elemento.id
      data.rotate = -90
      t.updateDocumento(data)
        .then(() => {
          t.elemento.refresh = _.now() // eslint-disable-line
        })
    },
    deleteParte (event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then((response) => {
          t.$parent.getDocumento(t.parent.id)
          t.success('Elemento excluído com sucesso.')
        })
        .catch((response) => {
          t.danger(response.response.data.detail)
        })
    }
  }
}
</script>

<style lang="scss" scoped>

.container-documento-edit {

  .tpd-file {
    border: 1px solid #aaa;
    position: relative;
    z-index: 1;
    padding: 5px;
    opacity: 0.8;
    transition: all 1s ease;
    margin:3px;
    position: relative;

    width: auto;
    min-width: 6em;
    &:hover {
      transition: all 0.3s ease;
      opacity: 1;
    }
    &.drag-start {
      opacity: 0.5;
      transition: all 1s ease;
      //transform: rotate(0.3);
    }
    &.drag-leave {
      opacity: 0.1;
      transition: all 1s ease;
    }
    &.drag-over {
      opacity: 0.3;
      transition: all 1s ease;
    }

    .btn-controls {
      position: absolute;
      right: 0;
      top: 0;
      z-index: 2;
      background-color: #ffffff33;
      margin: 5px;
      transition: all 1s ease;
      white-space: nowrap;
      cursor: pointer;
      &:hover {
        transition: all 1s ease;
        background-color: #ffffffbb;
      }
    }
    &:hover {
      transition: all 1s ease;
      .btn-controls {
        background-color: #ffffff99;
        transition: all 1s ease;
      }
    }

    .image-render {
      width: 100%;
      img {
        width: 100%;
        object-fit: cover;
      }
    }

    &.images-list {
    }
    &.files-list {
      margin-bottom: 10px;
      flex: 1 1 45%;
      border: 1px solid #aaa;
    }
  }
  .container-file {
    .tpd-file {
      &.draggable {
        z-index: 1;
        cursor: default;

        -moz-user-select: none;
        -khtml-user-select: none;
        -webkit-user-select: none;
        user-select: none;
        -khtml-user-drag: element;
        -webkit-user-drag: element;
      }
    }
  }
}
</style>
