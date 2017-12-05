<template lang="html">
  <div :class="classChild(elemento.id, elemento.tipo)">
    <div class="path-title-container">
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
.container, .container-fluid {
  border: 1px solid white;
  background: white;
}
</style>
