<template>
  <div class="individuo-aparteante-component">
    <div :class="['individuo-aparteante', ]"
      v-if="individuo && initCronometro"
      :key="`individuo-aparteante-${individuo.id}`"
      :ref="`individuo-aparteante-${individuo.id}`">
      <div class="inner-individuo">
        <div class="individuo-header">
          <div class="name">
          <strong>EM APARTE:</strong>
            {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
          </div>
        </div>
      </div>
      <div class="inner-individuo">
        <div class="individuo">
          <div class="avatar">
            <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
            <i v-else class="fas fa-user-circle fa-2x"></i>
          </div>
        </div>
        <div class="divide"></div>
        <div class="cronometro" >
          <div class="icon-status-microfone">
            <i v-if="individuo && individuo.status_microfone" class="fas fa-microphone"></i>
            <i v-else class="fas fa-microphone-slash"></i>
          </div>
          <cronometro-palavra
            :key="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :ref="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :cronometro_id="individuo.cronometro"
            :controls="[
              'toggleDisplay',
              'pause',
              'resume',
              'add30s',
              'add1m'
        ]"
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
  name: 'individuo-aparteante',
  components: {
    CronometroPalavra
  },
  props: {
    individuo_id: {
      type: Number,
      required: false,
      default: null
    }
  },
  data () {
    return {
      id: this.individuo_id,
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
  mounted () {
    console.log('Individuo Aparteante mounted')
    const t = this
    t.init = true
    t.fetch({
      app: t.app,
      model: t.model,
      id: t.id
    })
  },
  methods: {
    fetch (metadata) {
      setTimeout(() => {
        this._fetch(metadata)
      }, 100)
    },
    _fetch (metadata) {
      this
        .refreshState(metadata)
        .then((individuo) => {
          if (individuo) {
            this.individuo = individuo
            this.initCronometro = true
          } else if (individuo && this.individuo && individuo.id === this.individuo.id && !individuo.com_a_palavra) {
            this.individuo = null
          }
        })
    }
  }
}
</script>
<style lang="scss">
@media screen and (min-width: 992px) {
  .individuo-aparteante-component {
    .individuo-aparteante {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
      margin-left: 5em;
      .inner-individuo {
        display: flex;
        flex-direction: row;
        align-items: stretch;
        justify-content: flex-start;
        width: auto;
      }
      .individuo-header {
        text-align: left;
        font-size: 1.2em;
        color: #bb0;
        width: 100%;
        .name {
          background-color: #444;
          white-space: nowrap;
          margin: 0;
          padding: 7px 14px 6px;
          text-align: left;
          display: inline-block;
        }
      }
      .individuo {
        flex: 1 1 auto;
      }
      .divide {
        width: 1px;
        background-color: #888;
        margin: 0;
      }
      .cronometro {
        flex: 1 1 auto;
        padding: 1em;
        font-size: 0.8em;
        position: relative;
        .icon-status-microfone {
          position: absolute;
          top: 0.5em;
          left: 0.5em;
          font-size: 2em;
          color: #ccc;
          i {
            &.fa-microphone {
              color: #4c4;
            }
            &.fa-microphone-slash {
              color: #c44;
            }
          }
        }
      }
      .croncard {
        justify-content: center;
        gap: 1em;
      }
      .controls {
        &.visible {
          .btn-group {
            margin: 0;
            width: auto;
            .btn {
              padding: 0.3em 0.7em 0.2em 0.7em;
            }
          }
        }
      }
      .individuo {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 2em 1em;
        .avatar {
          opacity: 1 !important;
          width: 5em;
          height: 5em;
          img {
            box-shadow: 0px 0px 30px #444;
          }
          i {
            color: #ccc;
            font-size: 4em;
          }
        }
      }
    }
  }
}
</style>
