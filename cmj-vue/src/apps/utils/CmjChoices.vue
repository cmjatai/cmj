<template>
  <div class="radio-group" :id="name+id">
    <template v-for="(choice, k) in options">
        <label :class="['btn', choice.triple, k == value ? 'active': '']" v-bind:for="choice.triple">
          <input type="radio" v-bind:value="k" v-model="model" :id="choice.triple" :name="name+id">
            {{choice.text}}
        </label>
    </template>
  </div>
</template>

<script>
    export default {
        props: [
          'options',
          'value',
          'name',
          'id'
        ],
        data() {
          return {
              model: -1,
          };
        },
        watch: {
          model: function(val){
            this.$emit('input', parseInt(val))
          },
          value: function(val) {
            this.model = val
          }
        },
        mounted() {
          let t = this
          t.$nextTick()
            .then(function () {
              if (t.value !== undefined)
                t.model = t.value
            })

        }
    }
</script>

<style>
  .radio-group {
    display: inline-block;
    border-radius: 30px;
    overflow: hidden;
  }
  .radio-group input[type="radio"] {
      display: none;
  }
  .radio-group .btn {
    border-radius: 0px;
  }
</style>
