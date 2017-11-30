<template lang="html">
  <div class="container-path container-documento-edit">
    <div class="container">
        <div class="path-title construct">
          <input v-model.lazy="titulo" placeholder="Título do Documento"/>
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
      message: ''
    }
  },
  watch: {
    titulo: function(val) {
      let data = {
        id: this.id,
        titulo: this.titulo
      }
      this.setTitulo(data)
      this.documentoResource.setDocumento(data, 'set_titulo')
        .then( (response) => {
          this.message = response.data.message
        })
    },
    descricao: function(val) {
      let data = {
        id: this.id,
        descricao: this.descricao
      }
      this.setDescricao(data)
      this.documentoResource.setDocumento(data, 'set_descricao')
        .then( (response) => {
          this.message = response.data.message
        })
    }
  },
  computed: {
    ...mapGetters([
      'getDocObject', 'getChilds'
    ])
  },
  methods: {
    ...mapActions([
      'setDocObject',
      'setTitulo',
      'setDescricao',
    ]),
  },
  mounted: function() {
      let id = this.$route.params.id
      this.documentoResource.getDocumento(id)
        .then( (req) => {
          this.setDocObject(req.data)
          this.id = req.data.id
          this.titulo = req.data.titulo
          this.descricao = req.data.descricao
        })
        .catch( (e) => {
          this.message = 'erro erro erro'
          this.setDocObject([])
        })
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
