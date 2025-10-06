<template>
  <div class="palavraemuso-component">
    <div :class="['individuo-com-a-palavra', ]"
      v-if="individuo && initCronometro"
      :key="`individuo-com-a-palavra-${individuo.id}`"
      :ref="`individuo-com-a-palavra-${individuo.id}`">
      <div class="inner-individuo">
        <div class="individuo">
          <div class="name">
            {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
          </div>
          <div class="avatar">
            <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
            <i v-else class="fas fa-user-circle fa-2x"></i>
          </div>
        </div>
        <div class="divide"></div>
        <div class="cronometro" >
          <cronometro-palavra
            :key="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :ref="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :cronometro_id="individuo.cronometro"
            ></cronometro-palavra>
        </div>
      </div>
    </div>

  </div>
</template>
<script>
import Vuex from 'vuex'
import CronometroPalavra from '../components/cronometros/CronometroPalavra.vue'
export default {
  name: 'palavra-em-uso',
  components: {
    CronometroPalavra
  },
  data () {
    return {
      init: false,
      app: 'painelset',
      model: 'individuo',
      individuo: null,
      initCronometro: false
    }
  },
  computed: {
    ...Vuex.mapGetters([
      'getIndividuoComPalavra'
    ]),
    fotografiaParlamentarUrl: function () {
      if (this.individuo && this.individuo.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.individuo.parlamentar + '/fotografia.c96.png'
      }
      return null
    }
  },
  watch: {
    getIndividuoComPalavra: function (newVal, oldVal) {
      if (newVal !== oldVal) {
        console.log('getIndividuoComPalavra mudou', newVal, oldVal)
        this.individuo = newVal
        this.$nextTick(() => {
          setTimeout(() => {
            this.initCronometro = true
          }, 500)
        })
      }
    }
  },
  mounted () {
    console.log('PalavraEmUso mounted')
    const t = this
    t.init = true
  },
  methods: {
    fetch (metadata) {
      setTimeout(() => {
        this._fetch(metadata)
      }, 100)
    },
    _fetch (metadata) {
      this
        .getObject(metadata)
        .then((individuo) => {
          if (individuo && individuo.com_a_palavra) {
            this.individuo = individuo
          } else if (individuo && this.individuo && individuo.id === this.individuo.id && !individuo.com_a_palavra) {
            this.individuo = null
          }
        })
    }
  }
}
</script>
<style lang="scss">
.palavraemuso-component {
  display: flex;
  flex-direction: column;
  .individuo-com-a-palavra {
    background-color: #222;
    display: flex;
    flex-direction: column;
    min-height: 10vh;
  }
  .inner-individuo {
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
  }
  .individuo {
    flex: 1 1 0%;
  }
  .divide {
    width: 1px;
    background-color: #aaa;
    margin: 10px 0;
  }
  .cronometro {
    flex: 1 1 100%;
    padding: 10px;

  }
  .individuo {
    display: flex;
    flex-direction: column;
    justify-content: end;
    padding: 2em 1em;
    .avatar {
      opacity: 1 !important;
      width: 96px;
      height: 96px;
      img {
        box-shadow: 0px 0px 30px #555;
      }
      i {
        color: #ccc;
        font-size: 4em;
      }
    }
    .name {
      font-weight: bold;
      text-align: center;
      font-size: 1em;
      color: #fff;
      padding: 7px 14px 5px;
      background-color: #444;
      white-space: nowrap;
      position: absolute;
      top: 0;
      left: 0;
    }
  }
}

</style>
