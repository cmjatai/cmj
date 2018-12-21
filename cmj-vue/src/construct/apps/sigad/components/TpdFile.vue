<template lang="html">
  <div :class="[name_component, 'draggable', classDrag]"
    v-on:dragend="dragend"
    v-on:dragenter="dragenter"
    v-on:dragleave="dragleave"
    v-on:dragover="dragover"
    v-on:dragstart="dragstart"
    v-on:dragexit="dragexit"
    v-on:drop="drop"
    v-on:mouseover="mouseOver"
    v-on:mouseleave="mouseLeave">
      <img :src="slug+'.256?'+refresh">
      <div class="imgmouseover" v-if="false">
        <img :src="slug+'.512?'+refresh">
      </div>
      <div class="drag">
        <div class="btn-controls">
          <span class="btn btn-rotate"  v-on:click="rotateLeft" title="Rotacionar 90 graus a esquerda">
            <i class="fa fa-rotate-left" aria-hidden="true"></i>
          </span>
          <span class="btn btn-rotate"  v-on:click="rotateRight" title="Rotacionar 90 graus a direita">
            <i class="fa fa-rotate-right" aria-hidden="true"></i>
          </span>
          <span class="btn btn-delete"  v-on:click="deleteParte" >
            <i class="fa fa-trash" aria-hidden="true"></i>
          </span>
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
    z-index: 1;
    flex: 0 1 auto;
    flex-direction: row;
    padding: 5px;
    opacity: 0.8;
    transition: all 1s ease;
    margin:2px;
    position: relative;
    user-select:none;
    width: auto;
    &:hover {
      transition: all 0.3s ease;
      opacity: 1;
    }

    &.drag-start {
      opacity: 0.5;
      transition: all 1s ease;
    }
    &.drag-leave {
      opacity: 0.1;
      transition: all 1s ease;
    }
    &.drag-over {
      opacity: 0.2;
      transition: all 1s ease;
    }
    .drag {
      border: 1px solid #aaa;
      position: absolute;
      top: 0;
      left:0;
      right: 0;
      bottom: 0;
      display: block;
      z-index: 1;

      -moz-user-select: none;
      -khtml-user-select: none;
      -webkit-user-select: none;
      user-select: none;
      -khtml-user-drag: element;
      -webkit-user-drag: element;
    }
    .btn-controls {
      flex: 0 1 auto;
      z-index: 2;
      position: relative;
    }
  }
}
</style>
