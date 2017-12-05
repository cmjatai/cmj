<template lang="html">
  <div class="container">
    <div class="path-title construct">
      <textarea-autosize v-model.lazy="elemento.titulo" placeholder="Título..."/>
    </div>
    <component :is="classChild(key, value.tipo)" v-for="(value, key) in childs" :child="value" :parent="elemento" :key="key"/>
  </div>
</template>

<script>
import DocumentoEdit from './DocumentoEdit'
export default {
  name: 'container',
  extends: {
    ...DocumentoEdit,
  }
}
</script>

<style lang="scss" scoped>

</style>
