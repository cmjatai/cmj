<template lang="html">
  <div :class="[name_component, 'container']">

    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-sm">
      </div>
    </div>
    <div class="drop-area">
      <drop-zone v-on:change="changeImage" :elemento="elemento" :src="slug" :multiple="true" :resource="documentoResource"/>
    </div>
    <div class="inner">
      <modal-image-list v-if="showModal >= 0" @close="showModal = -1" :elementos="childsOrdenados" :child="showElemento" :pos="showModal" :parent="elemento" />
      <component :is="classChild(value)" v-on:ondragend="ondragend" v-on:ondragleave="ondragleave" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id" :pos="key" v-on:showmodal="showModalAction"/>
    </div>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'

export default {
  name: 'container-td-bi',
  extends: {
    ...DocumentoEdit
  },
  data () {
    return {
      dragleave: null,
      side: 0,
      showModal: -1,
      showElemento: null
    }
  },
  methods: {
    showModalAction (elemento, pos) {
      this.showElemento = elemento
      this.showModal = pos
    },
    ondragend: function (el) {
      console.log('ondragend: ContainerTdBi', el)
      if (el.id === this.dragleave.id) {
        return
      }
      let data = Object()
      data.id = el.id
      data.ordem = this.dragleave.ordem
      if (el.ordem > this.dragleave.ordem && this.side > 0) {
        data.ordem++
      } else if (el.ordem < this.dragleave.ordem && this.side < 0) {
        data.ordem--
      }
      if (el.ordem === data.ordem) {
        return
      }
      el.ordem = data.ordem
      this.updateDocumento(data)
        .then(() => {
          this.getDocumento(this.elemento.id)
        })
    },
    ondragleave: function (el, side) {
      console.log('ondragleave: ContainerTdBi', el, side)
      this.dragleave = el
      this.side = side
    },
    changeImage: function () {
      this.getDocumento(this.elemento.id)
    }
  }
}
</script>

<style lang="scss">

.container-documento-edit {
  .container-td-bi {
    & > .drop-area {
      padding: 0 10px;
    }
    & > .inner {
      padding: 5px;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      user-select:none;
    }
  }
}
</style>
