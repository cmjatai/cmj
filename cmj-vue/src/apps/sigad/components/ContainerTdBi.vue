<template lang="html">
  <div :class="[classChild(elemento), 'container']">

    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
      </div>
    </div>
    <div class="drop-area">
      <drop-zone v-on:change="changeImage" :elemento="elemento" :src="slug" :multiple="true" :resource="documentoResource"/>
    </div>
    <div class="inner">
      <component :is="classChild(value)" v-on:ondragend="ondragend" v-on:ondragleave="ondragleave" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
    </div>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'
import Container from './Container'

export default {
  name: 'container-td-bi',
  extends: {
    ...DocumentoEdit,
  },
  data() {
    return {
      dragleave: null,
      side: 0,
    }
  },
  methods: {
    ondragend: function(el) {
      if (el.id === this.dragleave.id) {
        return
      }

      let data = Object()
      data.id = el.id
      data.ordem = this.dragleave.ordem

      if (el.ordem > this.dragleave.ordem && this.side > 0) {
        data.ordem++
      }
      else if (el.ordem < this.dragleave.ordem && this.side < 0) {
        data.ordem--
      }

      if (el.ordem === data.ordem){
        return
      }

      el.ordem = data.ordem
      this.updateDocumento(data)
        .then( () => {
          this.getDocumento(this.elemento.id)
        })
    },
    ondragleave: function(el, side) {
      this.dragleave = el
      this.side = side
    },
    changeImage: function() {
      this.getDocumento(this.elemento.id)
    },
    deleteParte(event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then( (response) => {
          t.$parent.getDocumento(this.parent.id)
          t.success('Elemento excluído com sucesso.')
        })
        .catch( (response) => {
          t.danger(response.response.data.detail)
        })
    },
  },

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
