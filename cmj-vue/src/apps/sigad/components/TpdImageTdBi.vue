<template lang="html">
  <div :class="[classChild(elemento)]">

    
    <div v-if="elemento.has_midia">
      <img :src="slug+'.256'">
    </div>
  </div>
</template>

<script>
import TpdImage from './TpdImage'

export default {
  name: 'tpd-image-td-bi',
  extends: {
    ...TpdImage,
  },
}
</script>

<style lang="scss">
.container-documento-edit {
  & > .tpd-image-td-bi
   {
  }
}
</style>
