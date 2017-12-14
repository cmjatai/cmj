<template lang="html">
  <div :class="classParent">
    <div v-if="notHasParent" class="container">
      <div v-show="elemento.id" class="btn-toolbar widgets-function">
        <div class="btn-group btn-group-xs pull-left widget-actions ">
          <a :href="slug" class="btn btn-primary" target="_blank">Versão Final</a>
          <a :href="meta_edit" class="btn btn-success" target="_blank">Editar Metadados</a>
        </div>
        <div class="btn-group btn-group-lg pull-right widget-visibilidade">
          <cmj-choices v-model.lazy="elemento.visibilidade" :options="visibilidade_choice" name="visibilidade-" :id="elemento.id" />
        </div>
      </div>
        <div class="path-title construct">
          <textarea-autosize v-model.lazy="elemento.titulo" placeholder="Título do Documento"  :align="'text-center'"/>
        </div>
        <div class="path-description construct">
          <textarea-autosize v-model.lazy="elemento.descricao" placeholder="Descrição do Documento" :align="'text-center'"/>
        </div>
        <div class="construct">
          <textarea-autosize v-model.lazy="elemento.texto" placeholder="texto..." :align="'text-left'"/>
        </div>
      </div>
    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { DocumentoResource } from '../../../resources'
import { orderBy, isEmpty } from 'lodash';

export default {
  name: 'documento-edit',
  props: ['child', 'parent'], // props.child == data.elemento
  data() {
    return {
      documentoResource: DocumentoResource,
      elemento: {
        id: 0,
        classe: 0,
        parent: null,
        titulo: '',
        descricao: '',
        visibilidade: 99,
        texto: '',
      },
      mode: "INIT",
    }
  },
  watch: {
    'elemento.titulo': function(nv, ov) { this.handlerWatch(nv, ov, 'titulo') },
    'elemento.descricao': function(nv, ov) { this.handlerWatch(nv, ov, 'descricao') },
    'elemento.visibilidade': function(nv, ov) { this.handlerWatch(nv, ov, 'visibilidade') },
    'elemento.texto': function(nv, ov) { this.handlerWatch(nv, ov, 'texto') },
    parent:function(nv, ov) {
      this.elemento = this.child
    },
  },
  computed: {
    ...mapGetters([
       'getChilds',
       'getChoices',
       'getDocObject',
    ]),
    hasParent: function() {
      return this.elemento && this.elemento.parent > 0
    },
    notHasParent: function() {
      return !this.elemento || !this.elemento.parent
    },

    slug: function() {
      let slug = this.elemento.slug
      return '/'+slug
    },
    meta_edit: function() {
      let slug = this.getSlug
      return '/documento/'+this.elemento.id+'/edit'
    },
    childsOrdenados: function() {
      let ordenar = this.elemento.childs
      return _.orderBy(ordenar,'ordem')
    },
    visibilidade_choice: function() {
      return this.elemento.choices && this.elemento.choices.visibilidade
        ? this.elemento.choices.visibilidade : {}
    },
    classParent: function() {
      return this.notHasParent ? 'container-path container-documento-edit' : ''
    },
    ordem:function() {
      return this.elemento.ordem
    }

  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
      'sendMessage',
    ]),
    classChild(value) {
      if (!value.id && this.notHasParent)
        return 'container-path container-documento-edit'
      else {
        try {
          let classe = this.getDocObject.choices.all_bycode[value.tipo]['component_tag']
          if (this.getDocObject.tipo !== 0)
            classe += '-'+this.getDocObject.choices.all_bycode[this.getDocObject.tipo]['component_tag']
          return classe
        }
        catch (Exception) {
          return ''
        }
      }
    },
    handlerWatch(newValue, oldValue, attr=null) {
      let data = Object()
      if (attr)
          data[attr] = newValue

      if (this.mode === "CREATE") {
         data.classe = this.elemento.classe
         data.parent = this.elemento.parent
         this.createDocumento(data)
         return
      }
      else if (this.mode === "INIT") {
        return
      }

      data.id = this.elemento.id
      this.updateDocumento(data)
    },
    updateDocumento(data) {
      let t = this
      t.documentoResource.updateDocumento(data)
        .then( (response) => {
          t.setDocObject(response.data)
          t.success()
        })
        .catch( (response) => this.danger())
    },
    success(message='Informação atualizada com sucesso.') {
      this.sendMessage({alert:'alert-success', message:message})
    },
    danger(message='Ocorreu um erro na comunicação com o servidor.') {
      this.sendMessage({alert:'alert-danger', message: message })
    },
    createDocumento(data) {
      let t = this
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.setDocObject(response.data)
          t.$router.push({name:'documento_construct', params: {id:response.data.id}})
          t.$nextTick()
            .then(function() {
              t.getDocumento(response.data.id)
            })
        })
        .catch( (response) => this.danger())
    },
    getDocumento(id) {
      console.log('get:', id)
      let t = this
      this.mode = "INIT"
      this.$nextTick()
        .then(function() {
          t.documentoResource.getDocumento(id)
            .then( (req) => {
              t.setDocObject(req.data)
              t.elemento = req.data
              t.$nextTick()
                .then( function() {
                  t.mode = "UPDATE"
                  t.success()
                })
            })
            .catch( (e) => {
              t.setDocObject({})
              t.elemento = {}
              t.danger(message='erro na atualização')
            })
        })
    },
    createBrother(data) {
      let t = this
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.$parent.getDocumento(response.data.parent)
        })
        .catch( (response) => {
          t.danger()
        })
    },
    createChild(data) {
      let t = this
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.getDocumento(this.elemento.id)
        })
        .catch( (response) => {
          t.danger(message='erro na adição')
        })
    },

  },

  mounted: function() {
    let t = this
    if (t.child) {
      t.elemento = t.child
      t.$nextTick()
        .then( function() {
          t.mode = "UPDATE"
        })
    }
    else {
      let id = t.$route.params.id
      if (t.$route.name === 'documento_construct') {
        t.getDocumento(id)
      }
      else {
        t.mode = "CREATE"
        t.elemento.classe = id
        if (t.parent)
          t.elemento.parent = t.parent.id
      }
    }
  }
}
</script>

<style lang="scss" >
.container-path.container-documento-edit {
  background: #f7f7f7 url(/static/img/bg.png);
  padding: 20px 0px 200px;
  margin: -20px 0px 0;
  input, textarea {
    outline: none;
    width: 100%;
    margin: 5px 0;
    padding: 5px 10px;
    border: none;
    background: transparent;
    &:focus {
      background: transparentize(#fff, 0.7);
    }
  }
  .container:first-child {
    background-color: transparent;
    border: 1px solid transparent;
  }
  .path-title {
    margin-top: 1em;
    margin-bottom: 0;
  }
  .path-description {
    margin: 0px;
  }
  .widget-actions {
    a {
      color: white;
    }
  }
  .widget-visibilidade {
    .btn {
      opacity: 0.5;
      color: black;
      &:hover {
        opacity: 1;
      }
    }
    .active {
      opacity: 1;
      font-weight: bold;
      color: black;
    }
    .status-private {
      background: transparentize(#d90040,0.6);
    }
    .status-restrict {
      background: #ffd050;
    }
    .status-public {
      background: transparentize(#008020,0.6);
    }
  }
  .widgets {
    position: absolute;
    z-index: 2;
    width: 100%;
    transition: all 0.5s ease;
    opacity: 0;
    height: 0;
    display: none;
    &:hover {
      opacity: 1;
      transition: all 0.5s ease;
    }
  }
  .widget-bottom {
    top:100%;
    right:-10px;
    left: -10px;
    margin-top: -15px;
  }
  .widget-top {
    top: 0px;
    right:-10px;
    margin-top: -15px;
  }
  .tpd-texto, .tpd-audio, .tpd-video, .tpd-image {
    position: relative;
    padding-left: 10px;
    padding-right: 10px;
    margin-left: 10px;
    margin-right: 10px;
    border: 1px solid transparent;
    &:hover {
      background: transparentize(#fff, 0.4);
      border: 1px solid #fafafa;
      border-radius: 5px;
      & > .widgets {
        display: block;
        height: auto;
        opacity: 0.4;
        &:hover {
          opacity: 1;
          transition: all 0.5s ease;
        }
      }
    }
  }
  .fr-counter {
    display: none;
  }
}
</style>
