<template lang="html">
  <div :class="[name_component, 'container']">
    <span class="btn-pdf" >
      <b-button-group >
        <b-button v-if="childsOrdenados.length!=0" variant="primary">
          <i class="far fa-file-pdf" aria-hidden="true"  v-on:click.self="clickVersaoFinal"></i>
        </b-button>
      </b-button-group>
    </span>
    <div class="path-title-file construct">
      <input v-model.lazy="elemento.titulo" placeholder="Título do Arquivo..."/>
    </div>
    <div class="path-description-file construct">
      <input v-model.lazy="elemento.descricao" placeholder="Descrição do Arquivo..."/>
    </div>
    <div class="drop-area">
      <drop-zone v-on:change="changeImage" :elemento="elemento" :src="slug" :multiple="true" :resource="documentoResource"/>
    </div>
    <div class="inner">
      <!--modal-image-list v-if="showModal >= 0" @close="showModal = -1" :elementos="childsOrdenados" :child="showElemento" :pos="showModal" :parent="elemento" /-->
      <component :is="classChild(value)" v-on:ondragend="ondragend" v-on:ondragleave="ondragleave" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id" :pos="key" v-on:showmodal="showModalAction"/>
    </div>
    <div class="btn-toolbar widgets widget-bottom justify-content-end">
      <div class="btn-group btn-group-sm">
        <button v-on:click.self="addBrother('container', $event)" title="Adicionar novo Container Simples abaixo deste" type="button" class="btn btn-outline-primary">+C</button>
        <button v-on:click.self="addBrother('container-fluid', $event)" title="Adicionar novo Container Extendido abaixo deste"  type="button" class="btn btn-outline-primary">+CE</button>
        <button v-on:click.self="addBrother('container-file', $event)" title="Adicionar novo Container Para PDF"  type="button" class="btn btn-outline-primary">+CF</button>
      </div>
      <div class="btn-group btn-group-sm">
        <button v-on:click.self="deleteParte" title="Remover este Container" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
  </div>
</template>

<script>
import Container from './Container.vue'
export default {
  name: 'container-file',
  extends: {
    ...Container
  },
  data () {
    return {
      has_titulo: false,
      has_descricao: false,
      has_autor: false,
      dragleave: null,
      side: 0,
      showModal: -1,
      showElemento: null
    }
  },
  methods: {
    clickVersaoFinal () {
      window.open(this.slug, '_blank')
    },
    toogleTitulo (event) {
      this.has_titulo = !this.has_titulo
    },
    toogleDescricao (event) {
      this.has_descricao = !this.has_descricao
    },
    toogleAutor (event) {
      this.has_autor = !this.has_autor
    },
    addBrother (tipo, event) {
      let data = Object()
      data.tipo = this.getChoices.all_bycomponent[tipo].id
      data.parent = this.parent.id
      data.ordem = this.elemento.ordem + 1
      this.createBrother(data)
    },
    addChild (tipo, event) {
      let data = Object()
      data.tipo = this.getChoices.all_bycomponent[tipo].id
      data.parent = this.elemento.id
      this.createChild(data)
    },
    deleteParte (event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then((response) => {
          t.$parent.getDocumento(this.parent.id)
          t.success('Elemento excluído com sucesso.')
        })
        .catch((response) => {
          t.danger(response.response.data.detail)
        })
    },
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
    changeImage: function (response) {
      this.getDocumento(this.elemento.id)
    }
  }
}
</script>

<style lang="scss">

.container-documento-edit {
  .container-fluid  {
    width: 98%;
  }
  .container:first-child {
    background-color: transparent;
    border: 1px solid transparent;
  }
  .container, .container-fluid {
    position: relative;
    background-color: white;
    border: 1px solid #fafafa;
    background: transparentize(#bbb, 0.85);
    margin: 15px auto 30px;
    padding: 15px 0px 30px;
    &.empty {
      padding: 30px;
        & > .widgets {
        display: flex;
        height: auto;
        opacity: 0.4;
      }
    }
    & > .widget-bottom {
      margin-top: -15px;
      right: 10px;
    }
    &:hover {
      transition: all 0.5s ease;
      & > .widgets {
        transition: all 0.5s ease;
        display: flex;
        height: auto;
        opacity: 0.7;
        &:hover {
          opacity: 1;
          transition: all 0.5s ease;
        }
      }
    }
  }
  .container-file {
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
  .path-title-file {
    font-size: 130%;
  }
  .path-description-file {
    margin-bottom: 5px;
  }
  .btn-pdf {
    position: absolute;
    right: 10px;
    top: 0;
  }
}
</style>
