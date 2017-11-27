<template>
  <div>
    <h1>endereço 2 - {{endereco.message}}</h1>
    <a href="#" @click.prevent="prev">Anterior</a>
    <button v-on:click="next">Proxima</button>
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
  name: 'endereco2',
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
    ...mapActions([
      'setLoader',
    ]),
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
      //t.setLoader(true)
      axios.get("/api/enderecos.json",
      {
        params: {
          page: this.page,
        },
      })
      .then( (req) => this.lista = req.data.results )
      .then( () => {
        //t.setLoader(false)
      })
      .catch(function (error) {
        //  t.setLoader(false)
      });
      //setTimeout(function () {
      //}, 2000)
    }
  }
}
</script>
<style>
</style>
