<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento)]">
    <div class="btn-toolbar widgets widget-top">
      <div v-show="elemento.texto" class="btn-group btn-group-xs pull-left">
        <button  v-if="!elemento.titulo" v-on:click.self="toogleTitulo" title="Disponibilizar Título para a Imagem" type="button" class="btn btn-success">T</button>
        <button  v-if="!elemento.descricao" v-on:click.self="toogleDescricao" title="Disponibilizar Descrição para a Imagem" type="button" class="btn btn-success">D</button>
        <button  v-if="!elemento.autor" v-on:click.self="toogleDescricao" title="Disponibilizar Autor para a Imagem" type="button" class="btn btn-success">A</button>
      </div>
      <div class="btn-group btn-group-xs pull-right">
        <button v-on:click.self="deleteParte" title="Remover esta Imagem" type="button" class="btn btn-danger">x</button>
      </div>
    </div>
    <div class="btn-toolbar widgets widget-bottom">
      <div class="btn-group btn-group-xs pull-left">
        <button v-on:click.self="addBrother(tipo.component_tag, $event)" v-for="tipo, key in getChoices.tipo.subtipos" type="button" class="btn btn-default" title="Adiciona Elemento aqui...">{{tipo.text}}</button>
      </div>
    </div>

    <div class="inner">
      <span v-if="has_titulo || elemento.titulo" class="path-title-partes"><input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/></span>
      <input v-if="has_descricao || elemento.descricao" v-model.lazy="elemento.descricao" placeholder="Descrição da Imagem..."/>

      <div id="drop_zone" v-on:drop="drop_handler" v-on:dragover="dragover_handler" v-on:dragend="dragend_handler">
        <strong>Drag one or more files to this Drop Zone ...</strong>
      </div>




    </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import Container from './Container'

export default {
  name: 'tpd-image',
  extends: {
    ...Container,
  },
  components: {
  },
  data() {
    return {
    }
  },
  computed: {},
  methods: {
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
    position: relative;
    #drop_zone {
      border: 5px solid blue;
      width:  200px;
      height: 100px;
    }
    .btn-danger {
      border-radius: 50%;
    }
    .widgets {
      margin-top: 0px;
    }
    input.path-code {
      font-size: 50%;
      font-family: monospace;
      background: transparentize(#fff, 0.2);
      color: #22f;
      &::-webkit-input-placeholder { /* Chrome/Opera/Safari */
        color: #55b;
      }
      &::-moz-placeholder { /* Firefox 19+ */
        color: #55b;
      }
      &:-ms-input-placeholder { /* IE 10+ */
        color: #55b;
      }
      &:-moz-placeholder { /* Firefox 18- */
        color: #55b;
      }
    }
  }
}
</style>
