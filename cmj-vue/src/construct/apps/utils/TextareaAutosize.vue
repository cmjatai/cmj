<template>
  <textarea :class="align" ref="input" v-bind:value="value" placeholder="teste de placeholder" v-on:change="updateValue($event.target.value)"></textarea>
</template>
<script>
import autosize from 'autosize'
export default {
  props: ['value', 'align'],
  mounted () {
    let text = this.$el
    setTimeout(function () {
      autosize(text)
      autosize.update(text)
    }, 0)
  },
  methods: {
    updateValue: function (value) {
      this.$emit('input', value)
    }
  }
}
</script>
<style lang="scss" scoped>
  textarea {
    width: 100%;
    margin: 0;
    padding: 0;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
  }
</style>
