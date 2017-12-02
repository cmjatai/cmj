<template lang="html">
  <div class="container-path container-documento-edit">
    <div class="container">
        <div class="path-title construct">
          <textarea-autosize v-model.lazy="titulo" placeholder="Título do Documento"/>
        </div>
        <div class="path-description construct">
          <textarea-autosize v-model.lazy="descricao" placeholder="Descrição do Documento"/>
        </div>
    </div>
    <documento-edit-container-list v-for="child in getChilds" :child="child" :key="child.id"/>
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
       'getChilds'
    ])
  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
      'getDocObject',
    ]),
    updateDocumento(data) {
      if (!this.is_mounted)
        return
      data.id = this.id
      this.documentoResource.updateDocumento(data)
        .then( (response) => {
          this.message = ''
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


</style>
