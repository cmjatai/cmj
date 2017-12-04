<template lang="html">
  <div v-bind:class="classContainer">
    
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name:'documento-edit-container',
  props: ['child'],
  computed: {
    ...mapGetters([
        'getChoices',
        'getChilds',
        'getDocObject'
    ]),
    classContainer: function() {
      if (this.getChoices !== undefined)
        return this.getChoices.tipo.containers[this.child.tipo]['triple']
      else {
        return ''
      }
    }
  },
  methods: {
    ...mapActions([
       'setDocObject'
    ]),
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
