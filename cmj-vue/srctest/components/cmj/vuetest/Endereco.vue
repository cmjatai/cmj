<template>
  <div>
    <h1>endereço 1 -{{endereco.message}}</h1>
    <a href="#" @click.prevent="--page">Anterior</a>
    <button v-on:click="++page">Proxima</button>
    <div class="row" v-for="endereco in lista">
      <div class="col-xs-2">
        {{ endereco.pk }}
      </div>
      <div class="col-xs-10">
        {{ endereco.display }}
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import axios from 'axios'
export default {
  name: 'endereco',
  props: ['endereco'],
  data() {
    return {
      page: 0,
      lista: []
    }
  },
  mounted() {
    var page = parseInt(this.$route.query.page)
    page !== undefined && !isNaN(page) ? this.page = page : this.page = 1
  },
  watch: {
    page: function() {
      this.requestPagina()
    }
  },
  methods: {
    prev() {
      if (this.page !== 1) {
        this.page--
      }
    },
    next() {
      this.page += 1
    },
    requestPagina() {
      let t = this
      axios.get("/api/enderecos.json",
      {
        params: {
          page: t.page,
        },
      })
      .then( (req) => t.lista = req.data.results )
    }
  }
}
</script>
<style>
</style>
