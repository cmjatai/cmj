<template>
  <div id="exemplo">
    <table class="table">
      <thead>
        <th>pk</th>
        <th>Endereços</th>
      </thead>
      <tbody>
        <tr v-for="endereco in lista">
          <td>{{ endereco.pk }}</td>
          <td>{{ endereco.display }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script>
export default {
  data() {
    return {
      lista: []
    }
  },
  mounted() {
    this.$http.get("/api/enderecos.json").then( (req) => this.lista = req.data.results )
  },
}
</script>
<style>
</style>
