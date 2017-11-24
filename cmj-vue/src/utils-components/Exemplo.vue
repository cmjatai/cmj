<template>
  <table class="table">
    <thead>
      <th>pk</th>
      <th v-on:click="requestPagina">Endereços</th>
    </thead>
    <tbody>
      <tr v-for="endereco in lista">
        <td>{{ endereco.pk }}</td>
        <td>{{ endereco.display }}</td>
      </tr>
    </tbody>
  </table>
</template>
<script>
import { mapActions } from 'vuex';
export default {
  name: 'exemplo',
  data() {
    return {
      pagina: 1,
      lista: []
    }
  },
  mounted() {
    this.$http.get("/api/enderecos.json").then( (req) => this.lista = req.data.results )
  },
  methods: {
    ...mapActions([
      'setLoader',
    ]),
    requestPagina() {
      var _this = this;
      _this.setLoader(true);
      setTimeout(function () {
        _this.setLoader(false);

      }, 5000);
    }
  }
}

</script>
<style>
</style>
