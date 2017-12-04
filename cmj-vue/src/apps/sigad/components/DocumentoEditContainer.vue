<template lang="html">
  <div :class="classContainer">
teste
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name:'documento-edit-container',
  props: ['elemento'],
  computed: {
    ...mapGetters([
        'getChoices',
        'getChilds',
        'getDocObject'
    ]),
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
