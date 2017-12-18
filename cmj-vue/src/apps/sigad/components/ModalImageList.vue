<template lang="html">
  <div class="">
    <modal @close="$emit('close')">
      <template slot="header">
        <span class="path-title-partes">
          <input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/>
        </span>
      </template>
      <template slot="header-actions">
        <span class="btn btn-rotate"  v-on:click="rotateLeft" title="Rotacionar 90 graus a esquerda">
          <i class="fa fa-rotate-left" aria-hidden="true"></i>
        </span>
          <span class="btn btn-rotate"  v-on:click="rotateRight" title="Rotacionar 90 graus a direita">
            <i class="fa fa-rotate-right" aria-hidden="true"></i>
          </span>
        <span class="btn btn-delete"  v-on:click="deleteParte" >
          <i class="fa fa-trash" aria-hidden="true"></i>
        </span>
        <span class="btn btn-close"  @click="$emit('close')">
          <i class="fa fa-times" aria-hidden="true"></i>
        </span>
      </template>

      <template slot="body">
        <img :src="slug_local">
        <div v-if="pos !== elementos.length - 1" class="btn btn-direction btn-right" v-on:click="rightParte">
          <i class="fa fa-3x fa-chevron-right" aria-hidden="true"></i>
        </div>
        <div v-if="pos !==0" class="btn btn-direction btn-left" v-on:click="leftParte">
          <i class="fa fa-3x fa-chevron-left" aria-hidden="true"></i>
        </div>
      </template>
      <template slot="footer">
        <div class="path-description construct">
          <textarea v-model.lazy="elemento.descricao" placeholder="Descrição da Imagem..." :align="'text-left'"/>
        </div>
      </template>
    </modal>
  </div>
</template>

<script>
import ContainerTdBi from './ContainerTdBi'
export default {
  name: 'modal-image-list',
  extends: {
    ...ContainerTdBi,
  },
  data() {
    return {
      refresh: ''
    }
  },
  computed: {
    slug_local: function() {
      let r = this.refresh
      return ' /'+this.child.slug+'.1024' + (r ? '?'+r : '')
    },
  },
  props: ['elementos', 'pos',],
  methods: {
    rotateLeft: function() {
      let data = Object()
      data.id = this.elemento.id
      data.rotate = 90
      this.updateDocumento(data)
        .then( () => {
          this.refresh = _.now()
          //this.getDocumento(this.elemento.id)
        })
    },
    rotateRight: function() {
      let data = Object()
      data.id = this.elemento.id
      data.rotate = -90
      this.updateDocumento(data)
        .then( () => {
          this.refresh = _.now()
          //this.getDocumento(this.elemento.id)
        })
    },
    leftParte: function() {
      this.$parent.showModal -= 1
      this.$parent.showElemento = this.elementos[this.$parent.showModal]
      this.elemento = this.$parent.showElemento
    },
    rightParte: function() {
      this.$parent.showModal += 1
      this.$parent.showElemento = this.elementos[this.$parent.showModal]
      this.elemento = this.$parent.showElemento
    }
  },
}
</script>
<style lang="scss" scoped>
.modal-mask {
  input, textarea {
    color: white;
    height: 100%;
    top: 0;
    left: 0;
    width: 100%;
    margin: 0px;
    position: absolute;
    &:focus {
      background: transparentize(#fff, 0.9);
    }
  }
  .btn {
    color: #aaa;
    &:hover {
      color: white;
    }
  }
  .btn-direction {
    position: absolute;
    top: 40%;
  }
  .btn-left {
    left: 0px;
  }
  .btn-right {
    right: 0px;
  }
}
</style>
