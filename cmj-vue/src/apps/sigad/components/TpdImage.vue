<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento), 'path-imagem', alinhamento(elemento)]">
    <div class="btn-toolbar widgets widget-top">
      <div v-show="elemento.texto" class="btn-group btn-group-xs pull-left">
        <button  v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Título para a Imagem" type="button" class="btn btn-success">T</button>
        <button  v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para a Imagem" type="button" class="btn btn-success">D</button>
        <button  v-if="!elemento.autor" v-on:click.self="toogleDescricao" title="Disponibilizar Autor para a Imagem" type="button" class="btn btn-success">A</button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click="alinhar(key, $event)" v-for="alinhamento, key in getChoices.alinhamento" type="button" class="btn btn-primary" :title="alinhamento.text" v-html="icons[key]"></button>

        <button v-on:click.self="deleteParte" title="Remover esta Imagem" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-primary" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>

    <div class="inner">
      <span v-if="has_titulo || elemento.titulo" class="path-title-partes"><input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/></span>
      <input v-if="has_descricao || elemento.descricao" v-model.lazy="elemento.descricao" placeholder="Descrição da Imagem..."/>

      <div class="drop_files" :id="'drop_file'+elemento.id" v-on:drop="drop_handler" v-on:dragover="dragover_handler" v-on:dragend="dragend_handler">
        <label  class="drop_zone" :for="'input_file'+elemento.id">
          <span class="inner">
            Arraste sua imagem e solte aqui.<br>
            <small>Ou clique aqui para selecionar</small>
          </span>
        </label>
        <input type="file" name="file_image" :id="'input_file'+elemento.id"/>
        <div class="view">
          <img :src="slug" alt="">
        </div>
      </div>
    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import Container from './Container'
import { mapGetters } from 'vuex'

export default {
  name: 'tpd-image',
  extends: {
    ...Container,
  },
  components: {
  },
  data() {
    return {
      icons: {
        0: '<i class="fa fa-align-left" aria-hidden="true"></i>',
        1: '<i class="fa fa-align-justify" aria-hidden="true"></i>',
        2: '<i class="fa fa-align-right" aria-hidden="true"></i>',
        3: '<i class="fa fa-align-center" aria-hidden="true"></i>',
      }
    }
  },
  computed: {
    ...mapGetters([
       'getChoices',
    ]),
  },
  methods: {
    alinhamento: function(value)  {
      let al = value.alinhamento
      try {
        return this.getChoices.alinhamento[al]['component_tag']
      }
      catch (Exception) {
        return ''
      }
    },
    alinhar(alinhamento, ev) {
        let data = Object()
        data.alinhamento = alinhamento
        data.id = this.elemento.id
        this.elemento.alinhamento = alinhamento
        this.updateDocumento(data)
    },
    drop_handler(ev) {
      if (ev === undefined)
        return
      console.log("Drop");
      ev.preventDefault();
      // If dropped items aren't files, reject them
      var dt = ev.dataTransfer;
      if (dt.items) {
        // Use DataTransferItemList interface to access the file(s)
        for (var i=0; i < dt.items.length; i++) {
          if (dt.items[i].kind == "file") {
            var f = dt.items[i].getAsFile();
            console.log("... file[" + i + "].name = " + f.name);
          }
        }
      } else {
        // Use DataTransfer interface to access the file(s)
        for (var i=0; i < dt.files.length; i++) {
          console.log("... file[" + i + "].name = " + dt.files[i].name);
        }
      }
    },

    dragover_handler(ev) {
      console.log("dragOver");
      // Prevent default select and drag behavior
      ev.preventDefault();
    },

    dragend_handler(ev) {
      console.log("dragEnd");
      // Remove all of the drag data
      var dt = ev.dataTransfer;
      if (dt.items) {
        // Use DataTransferItemList interface to remove the drag data
        for (var i = 0; i < dt.items.length; i++) {
          dt.items.remove(i);
        }
      } else {
        // Use DataTransfer interface to remove the drag data
        ev.dataTransfer.clearData();
      }
    }
  },
}
</script>

<style lang="scss">
.container-documento-edit {
  & > .tpd-image {
    z-index: 3;
    &.alinhamento-justify {
      padding-top: 10px;
      padding-bottom: 10px;
    }
    &.alinhamento-center:hover {
      margin: 0 auto !important;
    }
    &:hover {
    }
    .drop_files {
      width:  100%;
      text-align: center;
      background: transparentize(#fff, 0.5);
      position: relative;
      min-height: 150px;
      input {
        visibility: hidden;
        position: fixed;
        top: -100px;
        left: -100px;
        height: 0px;
        width: 0px;
      }
    }
    .drop_zone {
      border: 3px dashed #cccfcc;
      cursor: pointer;
      position: absolute;
      line-height: 1;
      margin: 0;
      top: 0;
      left: 0;
      bottom: 0;
      right: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      background: transparentize(#fff, 0.5);
      span {
        color: black;
        small {
          color: #000080;
        }
      }
    }
  }
}
</style>
