<template>
  <div class="buscador-classe">aaaaaaaaaab
    <slot></slot>
  </div>
</template>
<script>
export default {
  name: 'BuscadorClasse',
  props: {
    classe_id: {
      type: [Number, String],
      required: true
    }
  }
}
</script>
<style lang="scss">
</style>
