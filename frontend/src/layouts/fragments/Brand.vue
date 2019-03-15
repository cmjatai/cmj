<template>
  <div class="w-100 d-flex inner-brand">
    <img :src="casa.logotipo !== undefined ? casa.logotipo : '@/assets/img/brasao_transp.gif'"/>
    <h6 class="title-brand">
      {{casa.nome}}<br>
      <small>SAPL - Sistema de Apoio ao Processo Legislativo</small>
    </h6>
  </div>
</template>

<script>
import Resources from '@/resources'
export default {
  name: 'brand',
  data () {
    return {
      utils: Resources.Utils,
      app: 'base',
      model: 'casalegislativa',

      casa: {}
    }
  },
  methods: {
    fetch () {
      let _this = this
      return _this.utils.getModelOrderedList(_this.app, _this.model, 'id')
        .then((response) => {
          _this.casa = response.data.results[0]
        })
    }
  },
  mounted: function () {
    this.fetch()
  }
}
</script>

<style lang="scss">
.inner-brand {
  height: 100%;
  align-items: center;
  img {
    width: auto;
    height: 100%;
  }
  .title-brand {
    display: inline-block;
    padding-left: 1rem;
    line-height: 1;
    margin: 0;
  }
}
</style>
