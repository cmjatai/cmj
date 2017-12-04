<template lang="html">
  <div class="container-path container-documento-edit">
    <div class="container">
        <div v-show="id" class="btn-toolbar widgets-function">
          <div class="btn-group btn-group-xs pull-left widget-actions ">
            <a :href="slug" class="btn btn-primary" target="_blank">Versão Final</a>
          </div>
          <div class="btn-group btn-group-lg pull-right widget-visibilidade">
            <cmj-choices v-model="visibilidade" :options="visibilidade_choice" name="visibilidade-" :id="id" />
          </div>
        </div>
        <div class="path-title construct">
          <textarea-autosize v-model.lazy="titulo" placeholder="Título do Documento"/>
        </div>
        <div class="path-description construct">
          <textarea-autosize v-model.lazy="descricao" placeholder="Descrição do Documento"/>
        </div>
    </div>
    <documento-edit-container v-for="(value, key) in getChilds" :child="value" :key="key"/>
    <span v-on:click.stop="clickteste">{{message}}</span>
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
      descricao: '',
      titulo: '',
      id: 0,
      message: 'message teste',
      classe: 0,
      is_mounted: false,
      parent: 0,
      visibilidade: -1
    }
  },
  watch: {
    titulo: function(newValue, oldValue) {
      let data = {titulo: newValue}
      this.id === 0 ? this.createDocumento(data) : this.updateDocumento(data)
    },
    descricao: function(newValue, oldValue) {
      let data = {descricao: newValue}
      this.id === 0 ? this.createDocumento(data) : this.updateDocumento(data)
    },
    visibilidade: function(newValue, oldValue) {
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
    visibilidade_choice: function() {
      if (this.getChoices)
       return this.getChoices.visibilidade
      else {
        return {}
      }
    }
  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
    ]),
    updateDocumento(data) {
      if (!this.is_mounted)
        return
      data.id = this.id
      console.log(data)
      this.documentoResource.updateDocumento(data)
        .then( (response) => {
          this.setDocObject(response.data)
        })
    },
    createDocumento(data) {
      let t = this
      data.classe = t.classe
      if (t.parent !== 0)
        data.parent = t.parent
      t.documentoResource.createDocumento(data)
        .then( (response) => {
          t.setDocObject(response.data)
          t.id = response.data.id
        })
    },
    getDocumento() {
      let t = this
      t.documentoResource.getDocumento(t.id)
        .then( (req) => {
          t.setDocObject(req.data)
          t.id = req.data.id
          t.classe = req.data.classe
          t.titulo = req.data.titulo
          t.descricao = req.data.descricao
          this.$nextTick()
            .then(function () {
              t.visibilidade = req.data.visibilidade
            })
            .then(function () {
              t.is_mounted = true
            })
        })
        .catch( (e) => {
          t.message = 'erro erro erro'
          t.setDocObject([])
        })
    },
  },
  mounted: function() {
      let id = this.$route.params.id
      if (this.$route.name === 'documento_construct') {
        this.id = id
        this.getDocumento(id)
      }
      else {
        this.classe = id
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
