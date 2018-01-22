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
      <modal-referencia-image-list v-if="showModal >= 0" @close="showModal = -1" :elementos="citaOrdenados" :child="showElemento" :pos="showModal" :parent="elemento" />
      <div :class="['row', 'row-gallery', 'row'+elemento.id ]">
        <div :class="['col-xs-8', 'col-bi-container', 'row'+elemento.id ]">


          <div class="row">
            <div class="col-xs-12">
              <input v-if="has_titulo || elemento.titulo"  v-model.lazy="elemento.titulo" placeholder="Título da Galeria..."/>
              <input v-if="has_descricao || elemento.descricao" v-model.lazy="elemento.descricao" placeholder="Descrição da Galeria..."/>
              <input v-if="has_autor || elemento.autor" v-model.lazy="elemento.autor" placeholder="Autor da Galeria..."/>
            </div>
            <div class="col-xs-12">
              <div class="row row-bi-select">
                <select v-model="bi_selected">
                  <option disabled value="">Escolha um Banco de Imagem</option>
                  <option :value="value.value"  v-for="(value, key) in bi_list">{{value.text}}</option>
                </select>
              </div>
              <div :class="['row', 'row-bi', 'row'+elemento.id ]">
                <tpd-image-td-bi v-on:ondragend="ondragendtransf" v-for="(value, key) in images_from_bi" :child="value" :parent="elemento" :key="value.id"/>
                 <resize-observer @notify="handleResize" />
              </div>
            </div>
          </div>
        </div>
        <div class="col-xs-4 col-referencias">
          <div :class="['row', 'row-referencias', 'row'+elemento.id ]" v-on:dragend="ondragendtransf">
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
      bi_selected: "",
      bi_object: Object(),
      bi_list: Array(),
      has_titulo: false,
      has_descricao:false,
      has_autor: false,
      fullHeight: document.documentElement.clientHeight
    }
  },
  watch: {
    "bi_selected": function(nv, ov) {
      let t = this
      this.documentoResource.getDocumento(nv)
        .then( (req) => {
          t.bi_object = req.data
          t.success()
        })
    }
  },
  computed: {
    images_from_bi: function() {
      let images = this.bi_object
      if (images.ordem === undefined)
        return
      images = _.orderBy(images.childs,'ordem')
      images = _.orderBy(images[0].childs,'ordem')
      return images
    },
    citaOrdenados: function() {
      let ordenar = this.elemento.cita
      return _.orderBy(ordenar,'ordem')
    },
  },
  mounted() {
    let t = this
    t.documentoResource.getDocumentoChoiceList(10, 1)
      .then( (response) => {
        t.bi_list = response.data.results
      })
      .catch( (response) => {
        t.danger()
      })
  },
  methods: {
    handleResize () {
      if (this.elemento.id !== 0) {
        let colbicontainer = document.querySelector('.col-bi-container.row'+this.elemento.id)
        let rowreferencia = document.querySelector('.row-referencias.row'+this.elemento.id)
        rowreferencia.style.minHeight = colbicontainer.clientHeight + 'px'
      }
    },
    toogleTitulo(event) {
      this.has_titulo = !this.has_titulo
    },
    toogleDescricao(event) {
      this.has_descricao = !this.has_descricao
    },
    toogleAutor(event) {
      this.has_autor = !this.has_autor
    },
    ondragendtransf: function(el) {
      let dragleave = this.dragleave
      this.dragleave = null
      if (el.tipo === 900) {
        // o item arrastado é um TpdImageTdBi - Imagem de Banco de Imagem

        if (dragleave && dragleave.tipo === undefined) {
          // o item no qual o item arrastado foi solto é um item de referencia
          let referencia = Object()
          referencia.referente = this.elemento.id
          referencia.referenciado = el.id
          referencia.ordem = dragleave.ordem
          if (this.side > 0)
            referencia.ordem++
          let data = Object()
          data.cita = Array()
          data.cita.push(referencia)
          data.id = this.elemento.id
          this.updateDocumento(data)
            .then( () => {
              this.getDocumento(this.elemento.id)
            })
        }
        else {
          // se foi solto na caixa row-referencias
          let referencia = Object()
          referencia.referente = this.elemento.id
          referencia.referenciado = el.id
          referencia.ordem = 0
          let data = Object()
          data.cita = Array()
          data.cita.push(referencia)
          data.id = this.elemento.id
          this.updateDocumento(data)
            .then( () => {
              this.getDocumento(this.elemento.id)
            })
        }
      }
    },
    ondragend: function(el) {
      let dragleave = this.dragleave
      this.dragleave = null
      if (!dragleave || el.id === dragleave.id || dragleave.tipo >= 0) {
        return
      }
      let referencia = Object()
      referencia.id = el.id
      referencia.ordem = dragleave.ordem
      if (el.ordem > dragleave.ordem && this.side > 0)
        referencia.ordem++
      else if (el.ordem < dragleave.ordem && this.side < 0)
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
      if (el.tipo >= 0) {
        this.dragleave = null
        this.side = 0
      }
      else {
        console.log('ondragleave: tpdgallery', el, side)
        this.dragleave = el
        this.side = side
      }
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
    .row-bi-select {
      margin-right: 0px;
      select {
        width: 100%;
        padding: 5px;
        margin-bottom: 10px;
      }
    }
    .row-bi {
        background: transparentize(#fff, 0.6);
        border: 1px solid #fafafa;
        min-height: 100px;
        margin-right: 0px;

        display: flex;
        flex-wrap: wrap;
        justify-content: center;
    }
    .col-bi-container {
      display: inline-block;
      float: none;
    }
    .col-referencias {
      display: inline-block;
      vertical-align: top;
      float: none;
      width: 32%;
      /*position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      display: inline-block;*/
    }
    .row-referencias {
      background: transparentize(#fff, 0.6);
      border: 2px dashed #cccfcc;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      padding: 10px 0;
      min-height: 100px;
      height: 100%;
      align-items: flex-start;
      align-content: flex-start;
    }
  }
}
</style>
