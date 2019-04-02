<template>
  <div class="btn-group ml-2 btn-group-sm nivel-detalhe" role="group" aria-label="First group">
    <a
      @click="changeNivel(nivel.nivel)"
      v-for="(nivel, key) in niveis"
      :class="['btn btn-outline-dark', nivel_detalhe === nivel.nivel ? 'active' : '']"
      :key="'nv'+key">{{nivel.text}}</a>
  </div>
</template>

<script>
import Vuex from 'vuex'
export default {
  name: 'nivel-detalhe',
  data () {
    return {
      niveis: [
        {
          text: '|',
          nivel: 1
        },
        {
          text: '||',
          nivel: 2
        },
        {
          text: '|||',
          nivel: 3
        },
        {
          text: '||||',
          nivel: 4
        }
      ]
    }
  },
  methods: {
    ...Vuex.mapActions([
      'setNivelDetalhe'
    ]),
    changeNivel (nivel) {
      this.setNivelDetalhe(nivel)
    },
    fetch () {

    }
  },
  mounted: function () {
    this.fetch()
  }
}
</script>

<style lang="scss">
</style>
