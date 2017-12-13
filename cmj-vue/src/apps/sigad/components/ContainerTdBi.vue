<template lang="html">
  <div :class="['container-documento-edit', classChild(elemento), 'container']">

    <div class="btn-toolbar widgets widget-top">
      <div class="btn-group btn-group-xs pull-right">
      </div>
    </div>

    <drop-zone v-on:change="changeImage" :elemento="elemento" :src="slug" :multiple="true" :resource="documentoResource"/>

    <component :is="classChild(value)" v-for="(value, key) in childsOrdenados" :child="value" :parent="elemento" :key="value.id"/>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'
import Container from './Container'

export default {
  name: 'container-td-bi',
  extends: {
    ...DocumentoEdit,
  },
  methods: {
    deleteParte(event) {
      let t = this
      t.documentoResource.deleteDocumento(this.elemento.id)
        .then( (response) => {
          t.$parent.getDocumento(this.parent.id)
          t.success('Elemento excluído com sucesso.')
        })
        .catch( (response) => {
          t.danger(response.response.data.detail)
        })
    },
  },

}
</script>

<style lang="scss">

.container-documento-edit {
  & > .container-td-bi {
    padding: 0px;
  }
}
</style>
