<template lang="html">
  <div class="container-path container-documento-edit">
    <div class="container">
        <div v-show="id" :class="['widgets-function', visibilidade_class]">
          <div class="widget-visibilidade">
            <button v-for="(value, key ) in visibilidade_choice"
              :class="[value.triple, key, visibilidade_class === value.triple ? 'active': '']"
                type="button"
                name="button"
                v-on:click.stop="updateVisibilidade(key)">
              {{value.text}}
            </button>

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
    <span>{{message}}</span>
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
      message: '',
      classe: 0,
      is_mounted: false,
      parent: 0
    }
  },
  watch: {
    titulo: function(newValue, oldValue) {
      let data = {titulo: newValue}
      this.setTitulo(data)
      this.id === 0 ? this.createDocumento(data) : this.updateDocumento(data)
    },
    descricao: function(newValue, oldValue) {
      let data = {descricao: newValue}
      this.setDescricao(data)
      this.id === 0 ? this.createDocumento(data) : this.updateDocumento(data)
    }
  },
  computed: {
    ...mapGetters([
       'getChilds',
       'getChoices',
       'getDocObject',
    ]),
    visibilidade_class: function() {
      if (this.getChoices)
        return this.getChoices['visibilidade'][
          this.getDocObject.visibilidade]['triple']
      else {
        return ''
      }
    },
    visibilidade: function() {
      return this.getDocObject.visibilidade
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
    updateVisibilidade(key) {
      if (this.getDocObject.visibilidade == key)
        return
      let data = {visibilidade: key}
      this.updateDocumento(data)
    },
    updateDocumento(data) {
      if (!this.is_mounted)
        return
      data.id = this.id
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
        })
        .then( () => this.is_mounted = true)
        .catch( (e) => {
          t.message = 'erro erro erro'
          t.setDocObject([])
        })
    }
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

<style lang="scss" scoped>
.container-documento-edit {
  background: #f7f7f7 url(/static/img/bg.png);
  padding: 10px 0px;
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
  font-size: 70%;
  text-align: right;
  &.status-private {
    border-top: 5px solid transparentize(#a00040,0.5);
  }
  &.status-restrict {
    border-top: 5px solid transparentize(#f0c040,0.5);
  }
  &.status-public {
    border-top: 5px solid transparentize(#008020,0.5);
  }
}

.widget-visibilidade {
  button {
    border: none;
    text-decoration: none;
    display: inline-block;
    cursor: pointer;
    padding: 0 20px;
    margin: 0px 3px;
    outline: none;
    opacity: 0.5;
    color: black;
    margin-bottom: 10px;
    &:hover {
      opacity: 1;
      color: white;
    }
  }
  .active {
    opacity: 1;
    font-weight: bold;
    color: white;
    padding: 5px 20px;
  }
  .status-private {
    background: transparentize(#a00040,0.5);
  }
  .status-restrict {
    background: transparentize(#f0c040,0.5);
  }
  .status-public {
    background: transparentize(#008020,0.5);
  }
}

</style>
