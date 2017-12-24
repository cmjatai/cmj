<template lang="html">
  <div :class="name_component">

    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
      </div>
    </div>
    <div class="inner">
      <modal-image-list v-if="showModal >= 0" @close="showModal = -1" :elementos="citaOrdenados" :child="showElemento" :pos="showModal" :parent="elemento" />
      <component :is="'tpd-image-td-bi'" v-on:ondragend="ondragend" v-on:ondragleave="ondragleave" v-for="(value, key) in citaOrdenados" :child="value" :parent="elemento" :key="value.id" :pos="key" v-on:showmodal="showModalAction"/>
    </div>
  </div>
</template>

<script>
import ContainerTdBi from './ContainerTdBi'
import { orderBy, isEmpty } from 'lodash';

export default {
  name: 'tpd-gallery',
  extends: {
    ...ContainerTdBi,
  },
  computed: {
    citaOrdenados: function() {
      let ordenar = this.elemento.cita
      return _.orderBy(ordenar,'ordem')
    },
  },
  methods: {
    showModalAction(elemento, pos) {
      this.showElemento = elemento
      this.showModal = pos
    },
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
          if (t.elementos.length === 1) {
            t.$parent.showModal = -1
            t.$parent.showElemento = null
          }
          else {
            if (t.pos === 0) {
              t.$parent.showElemento = t.elementos[1]
            }
            else {
              t.$parent.showElemento = t.elementos[t.pos-1]
              t.$parent.showModal = t.pos-1
            }
          }
          t.$parent.getDocumento(t.parent.id)
            .then(() => {
            })
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
  .tpd-gallery {
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
