<template lang="html">
  <div class="">
    <modal @close="$emit('close')">
      <template slot="header">
        <span class="path-title-partes">
          <input v-model.lazy="elemento.titulo" placeholder="Título da Imagem..."/>
        </span>
      </template>
      <template slot="body">
        <img :src="'/'+elemento.slug+'.1024'">
      </template>
      <template slot="footer">

      </template>
    </modal>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'
export default {
  name: 'modal-image-list',
  extends: {
    ...DocumentoEdit,
  },
  props: ['elementos', 'pos'],
  methods: {},
}
</script>
<style lang="scss">
.modal-mask {
  .path-title-partes {

  }
}
</style>
