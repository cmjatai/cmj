<template lang="html">
  <div class="container-path container-documento-edit">
    <div class="container">
        <div v-show="elemento.id" class="btn-toolbar widgets-function">
          <div class="btn-group btn-group-xs pull-left widget-actions ">
            <a :href="elemento.slug" class="btn btn-primary" target="_blank">Versão Final</a>
          </div>
          <div class="btn-group btn-group-lg pull-right widget-visibilidade">
            <cmj-choices v-model.lazy="elemento.visibilidade" :options="visibilidade_choice" name="visibilidade-" :id="elemento.id" />
          </div>
        </div>
        <div class="path-title construct">
          <textarea-autosize v-model.lazy="elemento.titulo" placeholder="Título do Documento"/>
        </div>
        <div class="path-description construct">
          <textarea-autosize v-model.lazy="elemento.descricao" placeholder="Descrição do Documento"/>
        </div>
    </div>
    <documento-edit-container v-for="(value, key) in childs" :elemento="value" :key="key"/>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { DocumentoResource } from '../../../resources'

export default {
  name: 'documento-edit',
  data() {
    return {
      documentoResource: DocumentoResource,
      elemento: {},
      is_mounted: false,
    }
  },
  watch: {
    'elemento.titulo': function(newValue, oldValue) {
      if (oldValue === undefined && this.elemento.id !== undefined)
        return
      let data = {titulo: newValue}
      this.elemento.id === undefined ? this.createDocumento(data) : this.updateDocumento(data)
    },
    'elemento.descricao': function(newValue, oldValue) {
      if (oldValue === undefined && this.elemento.id !== undefined)
        return
      let data = {descricao: newValue}
      this.elemento.id === undefined ? this.createDocumento(data) : this.updateDocumento(data)
    },
    'elemento.visibilidade': function(newValue, oldValue) {
      if (oldValue === undefined && this.elemento.id !== undefined)
        return
      let data = {visibilidade: newValue}
      this.updateDocumento(data)
    },
  },
  computed: {
    ...mapGetters([
       'getChilds',
       'getChoices',
       'getDocObject',
       'getSlug',
    ]),
    slug: function() {
      let slug = this.getSlug
      return '/'+slug
    },
    childs: function() {
      return this.elemento.childs
    },
    visibilidade_choice: function() {
      return this.elemento.choices && this.elemento.choices.visibilidade
        ? this.elemento.choices.visibilidade : {}
    }
  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
    ]),
    updateDocumento(data) {
      let t = this
      if (!t.is_mounted)
        return
      data.id = t.elemento.id
      console.log(data)
      t.documentoResource.updateDocumento(data)
        .then( (response) => {
          t.setDocObject(response.data)
          t.elemento = response.data
        })
    },
    createDocumento(data) {
      let t = this
      data.classe = t.elemento.classe
      if (t.elemento.parent !== 0)
        data.parent = t.elemento.parent
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.setDocObject(response.data)
          t.elemento = response.data
          t.$router.push({name:'documento_construct', params: {id:response.data.id}})
        })
    },
    getDocumento(id) {
      let t = this
      t.documentoResource.getDocumento(id)
        .then( (req) => {
          t.setDocObject(req.data)
          t.elemento = req.data
          t.$nextTick()
            .then(function () {
              t.is_mounted = true
            })
        })
        .catch( (e) => {
          t.setDocObject({})
          t.elemento = {}
        })
    },
  },
  mounted: function() {
      let id = this.$route.params.id
      if (this.$route.name === 'documento_construct') {
        this.getDocumento(id)
      }
      else {
        this.elemento.classe = id
        this.is_mounted = true
      }
  }
}
</script>

<style lang="scss">
.container-documento-edit {
  background: #f7f7f7 url(/static/img/bg.png);
  padding: 20px 0px;
  margin: -20px 0px 0;
  input {
    outline: none;
  }
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
