
<template>
  <div id="app">
    <a href="#" @click.prevent="pushEnd">inserir novo componente endereço</a> |
    <a href="#" @click.prevent="pushEnd2">inserir novo componente endereço2</a>
    <a href="#" @click.prevent="trocarPrimeiro">Trocar Primeiro</a>
    <!--router-view class="view"></router-view-->
    <div v-for="end in enderecos">
      <component v-bind:is="end.component" v-bind:endereco="end"/>
    </div>
  </div>
</template>

<script>

  import { mapGetters } from 'vuex'

  export default {
    name: 'app',
    data() {
      return {
        enderecos: []
      }
    },
    computed: {},
    methods: {
      trocarPrimeiro() {
        this.enderecos.splice(0, 1, {component:'Endereco2', message:'trocou o primeiro por endereço2'})
      },
      pushEnd() {
        this.enderecos.push( {component:'Endereco', message:'inseriu endereço'})
      },
      pushEnd2() {
        this.enderecos.push( {component:'Endereco2', message:'inseriu endereço2'})
      }
    }
  };
</script>


<style lang="scss">
  @import "./scss/app.scss"
</style>
