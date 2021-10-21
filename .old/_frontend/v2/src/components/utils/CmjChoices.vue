<template>
  <div class="radio-group" :id="name+id">
    <template v-for="(choice, k) in options">
        <label :class="[choice.component_tag, k == value ? 'active': '']" v-bind:for="choice.component_tag" v-bind:key="k">
          <input type="radio" v-bind:value="k" v-model="model" :id="choice.component_tag" :name="name+id">
            {{choice.text}}
        </label>
    </template>
  </div>
</template>

<script>
export default {
  name: 'cmj-choices',
  props: [
    'options',
    'value',
    'name',
    'id'
  ],
  data () {
    return {
      model: -1
    }
  },
  watch: {
    model: function (val) {
      this.$emit('input', parseInt(val))
    },
    value: function (val) {
      this.model = val
    }
  },
  mounted () {
    let t = this
    t.$nextTick()
      .then(function () {
        if (t.value !== undefined) {
          t.model = t.value
        }
      })
  }
}
</script>

<style lang="scss">
.radio-group {
  display: inline-block;
  border-radius: 30px;
  overflow: hidden;
  border: 1px solid transparent;
  input[type="radio"] {
    display: none;
  }
  label {
    margin: 0;
    background: rgba(#ccc, 0.3);
    padding: 0 15px;
    &.active {
      background: rgba(#ccc, 0.7);
    }
  }
}
</style>
