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
        <textarea-autosize v-model.lazy="elemento.texto" placeholder="texto..." :align="'text-left'"/>
      </div>
    <component :is="classChild(key, value.tipo)" v-for="(value, key) in childs" :child="value" :parent="elemento" :key="key"/>

  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { DocumentoResource } from '../../../resources'

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
      mode: "INIT"
    }
  },
  watch: {
    'elemento.titulo': function(nv, ov) { this.handlerWatch(nv, ov, 'titulo') },
    'elemento.descricao': function(nv, ov) { this.handlerWatch(nv, ov, 'descricao') },
    'elemento.visibilidade': function(nv, ov) { this.handlerWatch(nv, ov, 'visibilidade') },
    'elemento.texto': function(nv, ov) { this.handlerWatch(nv, ov, 'texto') },
  },
  computed: {
    ...mapGetters([
       'getChilds',
       'getChoices',
       'getDocObject',
       'getSlug',
    ]),
    hasParent: function() {
      return this.elemento && this.elemento.parent > 0
    },
    notHasParent: function() {
      return !this.elemento || !this.elemento.parent
    },

    slug: function() {
      let slug = this.getSlug
      return '/'+slug
    },
    meta_edit: function() {
      let slug = this.getSlug
      return '/documento/'+this.elemento.id+'/edit'
    },
    childs: function() {
      return this.elemento.childs
    },
    visibilidade_choice: function() {
      return this.elemento.choices && this.elemento.choices.visibilidade
        ? this.elemento.choices.visibilidade : {}
    },
    classParent: function() {
      if (this.notHasParent)
        return 'container-path container-documento-edit'
      else {
        return ''
      }
    },
  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
    ]),

    classChild(id, tipo) {
      if (!id && this.notHasParent)
        return 'container-path container-documento-edit'
      else {
        try {
          return this.getDocObject.choices.all[tipo]['component_tag']
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
        })
    },
    createDocumento(data) {
      let t = this
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.mode = "UPDATE"
          t.setDocObject(response.data)
          t.$router.push({name:'documento_construct', params: {id:response.data.id}})
          t.$nextTick()
            .then(function() {
              t.getDocumento(response.data.id)
            })
        })
    },
    getDocumento(id) {
      let t = this
      t.documentoResource.getDocumento(id)
        .then( (req) => {
          t.setDocObject(req.data)
          t.elemento = req.data
        })
        .catch( (e) => {
          t.setDocObject({})
          t.elemento = {}
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
        t.$nextTick()
          .then( function() {
            t.mode = "UPDATE"
          })
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
  padding: 20px 0px;
  margin: -20px 0px 0;
  input {
    outline: none;
  }
  .path-title {
    margin-top: 1em;
    margin-bottom: 0;
    &.construct {
      input {
        width: 100%;
        background: transparent;
        border: 0px;
        line-height: 1;
        padding: 10px;
        text-align: center;
      }
    }
  }
  .path-description {
    margin: 0px;
  }
}

.widgets-function {
}
.widget-actions {
  a {
    color: white;
  }
}

.widget-visibilidade {
  .btn {
    opacity: 0.3;
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

</style>
