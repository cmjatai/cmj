<template lang="html">
  <div :class="name_component">
    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-left">
        <button v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Título para a Galeria" type="button" class="btn btn-success">T</button>
        <button v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para a Galeria" type="button" class="btn btn-success">D</button>
        <button v-if="!elemento.autor" v-on:click.self="toogleAutor" title="Disponibilizar Autor para a Galeria" type="button" class="btn btn-success">A</button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover esta Galeria" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="inner">
      <input v-if="has_titulo || elemento.titulo"  v-model.lazy="elemento.titulo" placeholder="Título da Galeria..."/>
      <input v-if="has_descricao || elemento.descricao" v-model.lazy="elemento.descricao" placeholder="Descrição da Galeria..."/>
      <input v-if="has_autor || elemento.autor" v-model.lazy="elemento.autor" placeholder="Autor da Galeria..."/>
      <modal-referencia-image-list v-if="showModal >= 0" @close="showModal = -1" :elementos="citaOrdenados" :child="showElemento" :pos="showModal" :parent="elemento" />
      <div class="row">
        <div class="col-xs-8">
            <div class="row-bancos-imagens">
            </div>
        </div>
        <div class="col-xs-4">
          <div class="row row-referencias">
            <tpd-referencia v-on:ondragend="ondragend" v-on:ondragleave="ondragleave" v-for="(value, key) in citaOrdenados" :child="value" :parent="elemento" :key="value.id" :pos="key" v-on:showmodal="showModalAction"/>
          </div>
        </div>
      </div>
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
  data() {
    return {
      has_titulo: false,
      has_descricao:false,
      has_autor: false,
    }
  },
  computed: {
    citaOrdenados: function() {
      let ordenar = this.elemento.cita
      return _.orderBy(ordenar,'ordem')
    },
  },
  methods: {
    toogleTitulo(event) {
      this.has_titulo = !this.has_titulo
    },
    toogleDescricao(event) {
      this.has_descricao = !this.has_descricao
    },
    toogleAutor(event) {
      this.has_autor = !this.has_autor
    },
    showModalAction(elemento, pos) {
      this.showElemento = elemento
      this.showModal = pos
    },
    ondragend: function(el) {
      if (el.id === this.dragleave.id) {
        return
      }

      let referencia = Object()
      referencia.id = el.id
      referencia.ordem = this.dragleave.ordem
      if (el.ordem > this.dragleave.ordem && this.side > 0)
        referencia.ordem++
      else if (el.ordem < this.dragleave.ordem && this.side < 0)
        referencia.ordem--
      if (el.ordem === referencia.ordem)
        return
      el.ordem = referencia.ordem

      let data = Object()
      data.cita = Array()
      data.cita.push(referencia)
      data.id = this.elemento.id

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
.container-path.container-documento-edit {
  .tpd-gallery {
    padding: 0 10px;
    &:hover {
      background: transparent;
      border: 1px solid transparent;
    }
    & > .inner {
      user-select:none;
    }
    .row-bancos-imagens {
        background: transparentize(#fff, 0.6);
        border: 1px solid #fafafa;
    }
    .row-referencias {
      background: transparentize(#fff, 0.6);
      border: 2px dashed #cccfcc;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      padding: 10px 0;
      min-height: 100px;
    }
  }
}
</style>
