<template>
  <div class="w-100 d-flex inner-brand">
    <img :src="casa.logotipo !== undefined ? casa.logotipo : require('@/assets/img/brasao_transp.gif')"/>
    <h6 class="title-brand">
      {{casa.nome}}<br>
      <small>SAPL - Sistema de Apoio ao Processo Legislativo</small>
    </h6>
  </div>
</template>

<script>
export default {
  name: 'brand',
  data () {
    return {
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
          if (response.data.results.length > 0) {
            _this.casa = response.data.results[0]
          }
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
    height: 48px;
  }
  .title-brand {
    display: inline-block;
    padding-left: 1rem;
    margin: 0;
    font-size: 110%;
  }
}

@media screen and (max-width: 800px) {
  .inner-brand {
    img {
      height: 40px;
    }
    .title-brand {
      //font-size: 100%;
      padding-left: 0.5rem;
    }
  }
}

@media screen and (max-width: 600px) {

  .inner-brand {
    img {
      height: 36px;
    }
    .title-brand {
      //font-size: 90%;
      padding-left: 0.25rem;
    }
  }

}
@media screen and (max-width: 480px){
  .inner-brand {
    img {
      height: 32px;
    }
    .title-brand {
      line-height: 1;
    }
  }
}

</style>
