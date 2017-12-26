<template lang="html">
  <div :class="['tpd-referencia', 'draggable', classDrag, 'col-xs-6']"
    v-on:dragend="dragend"
    v-on:dragenter="dragenter"
    v-on:dragleave="dragleave"
    v-on:dragover="dragover"
    v-on:dragstart="dragstart">
      <img :src="slug+'.128'">
      <div class="drag" @click="$emit('showmodal', child, pos)"></div>
      <span class="btn-delete"  v-on:click="deleteReferencia" title="Excluir esta referência">
        <i class="fa fa-remove" aria-hidden="true"></i>
      </span>
  </div>
</template>

<script>
import { DocumentoResource } from '../../../resources'
export default {
  name: 'tpd-referencia',
  props:['pos', 'child', 'parent'],
  data() {
    return {
      documentoResource: DocumentoResource,
      dragged: false,
      draggedover: 0,
      draggedleave: false,
    }
  },
  computed: {
    classDrag: function() {
      let classes = Array()
      this.dragged ? classes.push('drag-start') : ''
      this.draggedleave ? classes.push('drag-leave') : ''
      this.draggedover !== 0 ? classes.push('drag-over') : ''
      return classes
    },
    slug: function() {
      let slug = this.child.slug
      return '/'+slug
    },
  },
  methods: {
    dragend(ev) {
      if (this.dragged)
        this.$emit('ondragend', this.child)
      this.dragged = false
      this.draggedleave = false;
      this.draggedover = 0;
    },
    dragenter(ev) {
      if (this.dragged)
        this.draggedleave = false
    },
    dragleave(ev) {
      this.$emit('ondragleave', this.child, this.draggedover)
      this.draggedleave = this.dragged
      this.draggedover = 0
    },
    dragover(ev) {
      if (!this.dragged) {
          this.draggedover = ev.offsetX - ev.target.offsetWidth / 2
      }
    },
    dragstart(ev) {
      this.dragged = true
    },
    deleteReferencia(event) {
      let t = this
      let data = Object()
      let referencia = Object()
      referencia.id = this.child.id
      data.id = this.child.referente
      data.cita = Array()
      data.cita.push(referencia)
      t.documentoResource.deleteReferencia(data)
        .then( (response) => {
          t.$parent.success('Elemento excluído com sucesso.')
          t.$parent.getDocumento(t.parent.id)
        })
        .catch( (response) => {
          if (response.response)
            t.$parent.danger(response.response.data.detail)
          else
            t.$parent.danger(response.message)
        })
    },
  }
}
</script>

<style lang="scss">
.container-documento-edit {
  .tpd-referencia {
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

      .btn-delete {
        opacity: 0.7;
        color: transparentize(white, 0.1);
      }
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

      -moz-user-select: none;
      -khtml-user-select: none;
      -webkit-user-select: none;
      user-select: none;
      -khtml-user-drag: element;
      -webkit-user-drag: element;
    }

    .btn-delete {
      cursor: pointer;
      position: absolute;
      top: 6px;
      right: 6px;
      line-height: 16px;
      background: #ac2925;
      color: transparentize(black, 0.2);
      border-radius: 50%;
      width: 16px;
      height: 16px;
      font-size: 50%;
      text-align: center;
      opacity: 0.3;
      &:hover {
        opacity: 1;
        color: white;
      }
    }
  }
}
</style>
