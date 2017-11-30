<template lang="html">
  <div v-bind:class="classObject">
      {{child.id}}
  </div>
</template>

<script>
export default {
  name:'documento-edit-container-list',
  props: ['child'],
  computed: {
    classObject: function() {
      let container_type = {
        700: 'container',
        701: 'container-fluid'
      }
      return container_type[this.child.tipo]
    }
  }
}
</script>

<style lang="scss" scoped>
  .container, .container-fluid {
    background: white;
    margin-bottom: 10px;
  }
  .container {
    width: 70%;
  }
  .container-fluid {
    width: 95%;
    margin: 0 auto;
  }
</style>
