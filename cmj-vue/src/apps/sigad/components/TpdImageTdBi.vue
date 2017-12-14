<template lang="html">
  <div :class="[classChild(elemento)]">
      <img :src="slug+'.256'">
  </div>
</template>

<script>
import Container from './Container'

export default {
  name: 'tpd-image-td-bi',
  extends: {
    ...Container,
  },
}
</script>

<style lang="scss">
.container-documento-edit {
  .tpd-image-td-bi {
    flex: 0 1 auto;
    flex-direction: row;
    padding: 10px;
  }
}
</style>
