<template>
  <div class="nivel-detalhe">
    <span>
      Visões da Pauta
    </span>
    <div class="btn-group ml-2 btn-group-sm" role="group" aria-label="First group">
      <a
      @click="changeNivel(nivel.nivel)"
      v-for="(nivel, key) in niveis_filter"
      :class="['btn btn-outline-dark', nivel_detalhe === nivel.nivel ? 'active' : '']"
      :key="'nv'+key">{{nivel.text}}</a>
    </div>
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
          text: 'Resumida',
          nivel: 1
        },
        {
          text: 'Detalhada',
          nivel: 2
        },
        {
          text: 'Rito',
          nivel: 3
        }
        // {
        //  text: '||||',
        //  nivel: 4
        // }
      ]
    }
  },
  computed: {
    niveis_filter: function () {
      return this.niveis // .filter(i => i.nivel === 4 || i.nivel === 1)
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
.nivel-detalhe {
  position: sticky;
  margin: -15px -5px 0 0;
  top: 0px;
  z-index: 1;
  text-align: right;
  height: 0;
  opacity: 0.8;
  a.btn {
    padding: 3px 15px;
    line-height: 1;
  }
  span {
    color: #444;
    padding-right: 10px;
    display: block;
    background-color:#f0f0f0;
    background-image: url("~@/assets/img/bg.png");
  }
}
</style>
