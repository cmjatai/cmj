<template lang="html">
  <div class="">
    <modal @close="$emit('close')">
      <template slot="header">
        <span class="path-title-partes">
          <input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/>
        </span>
      </template>
      <template slot="header-actions">
        <span class="btn btn-lg btn-delete"  v-on:click="deleteParte" >
          <i class="fa fa-trash" aria-hidden="true"></i>
        </span>
        <span class="btn btn-lg btn-close"  @click="$emit('close')">
          <i class="fa fa-times" aria-hidden="true"></i>
        </span>
      </template>

      <template slot="body">
        <img :src="'/'+elemento.slug">
        <div v-if="pos !== elementos.length - 1" class="btn btn-direction btn-right" v-on:click="rightParte">
          <i class="fa fa-3x fa-chevron-right" aria-hidden="true"></i>
        </div>
        <div v-if="pos !==0" class="btn btn-direction btn-left" v-on:click="leftParte">
          <i class="fa fa-3x fa-chevron-left" aria-hidden="true"></i>
        </div>
        <div class="autor-imagem">
          <input v-model.lazy="elemento.autor" placeholder="Autor da Imagem..."/>
        </div>
      </template>
      <template slot="footer">
        <div class="path-description construct">
          <textarea v-model.lazy="elemento.descricao" placeholder="Descrição da Imagem..." :align="'text-left'"/>
        </div>
      </template>
    </modal>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { DocumentoResource } from '../../../resources'
export default {
  name: 'modal-referencia-image-list',
  props: ['elementos', 'pos', 'child', 'parent'],
  data() {
    return {
      documentoResource: DocumentoResource,
      elemento:this.child,
      ready: Array()
    }
  },
  watch: {
    'elemento.titulo': function(nv, ov) { this.handlerWatch(nv, ov, 'titulo') },
    'elemento.descricao': function(nv, ov) { this.handlerWatch(nv, ov, 'descricao') },
    'elemento.autor': function(nv, ov) { this.handlerWatch(nv, ov, 'autor') },
    parent:function(nv, ov) {this.elemento = this.child},
  },
  computed: {
  },
  methods: {
    ...mapActions([
      'sendMessage',
    ]),
    handlerWatch(newValue, oldValue, attr=null) {
      if (this.ready.indexOf(attr) === -1) {
        this.ready.push(attr)
        return
      }

      let data = Object()
      let referencia = Object()
      referencia.id = this.elemento.id
      if (attr)
          referencia[attr] = newValue

      data.id = this.elemento.referente
      data.cita = Array()
      data.cita.push(referencia)

      let t = this
      t.updateDocumento(data)
      .then( () => {
        t.success()
      })
    },
    updateDocumento(data) {
      let t = this
      return t.documentoResource.updateDocumento(data)
        .then( (response) => {

        })
        .catch( (response) => this.danger())
    },
    success(message='Informação atualizada com sucesso.') {
      this.sendMessage({alert:'alert-success', message:message})
    },
    danger(message='Ocorreu um erro na comunicação com o servidor.') {
      this.sendMessage({alert:'alert-danger', message: message })
    },

    leftParte: function() {
      this.ready = Array()
      this.$parent.showModal -= 1
      this.$parent.showElemento = this.elementos[this.$parent.showModal]
      this.elemento = this.$parent.showElemento
    },
    rightParte: function() {
      this.ready = Array()
      this.$parent.showModal += 1
      this.$parent.showElemento = this.elementos[this.$parent.showModal]
      this.elemento = this.$parent.showElemento
    },
    deleteParte(event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then( (response) => {
          if (t.elementos.length === 1) {
            t.$parent.showModal = -1
            t.$parent.showElemento = null
          }
          else {
            if (t.pos === 0) {
              t.$parent.showElemento = t.elementos[1]
            }
            else {
              t.$parent.showElemento = t.elementos[t.pos-1]
              t.$parent.showModal = t.pos-1
            }
          }
          t.$parent.getDocumento(t.parent.id)
            .then(() => {
            })
          t.success('Elemento excluído com sucesso.')
        })
        .catch( (response) => {
          t.danger(response.response.data.detail)
        })
    },
  },
}
</script>
<style lang="scss" scoped>
.modal-mask {
  input, textarea {
    color: white;
    height: 100%;
    top: 0;
    left: 0;
    width: 100%;
    margin: 0px;
    position: absolute;
    &:focus {
      background: transparentize(#fff, 0.9);
    }
  }
  .btn {
    color: #ccc;
    &:hover {
      color: white;
      background: transparentize(#fff, 0.7);
    }
  }
  .btn-direction {
    position: absolute;
    top: 40%;
  }
  .btn-left {
    left: 5px;
  }
  .btn-right {
    right: 7px;
  }
}
</style>
