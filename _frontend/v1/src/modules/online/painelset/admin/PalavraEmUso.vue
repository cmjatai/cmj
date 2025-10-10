<template>
  <div class="palavraemuso-component">
    <div :class="['individuo-com-a-palavra', ]"
      v-if="instance"
      :key="`individuo-com-a-palavra-${instance.id}`"
      :ref="`individuo-com-a-palavra-${instance.id}`">
      <div class="inner-individuo">
        <div class="individuo-header">
          <div class="name">
            {{ instance ? instance.name : 'Carregando indivíduo...' }}
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
        <div class="cronometro">
          <div class="icon-status-microfone">
            <i v-if="instance && instance.status_microfone" class="fas fa-microphone"></i>
            <i v-else class="fas fa-microphone-slash"></i>
          </div>
          <cronometro-palavra
            :key="`cronometro-com-a-palavra-${instance.cronometro}`"
            :ref="`cronometro-com-a-palavra-${instance.cronometro}`"
            :cronometro_id="instance.cronometro"
            ></cronometro-palavra>
        </div>
      </div>
    </div>
    <individuo-aparteante
      v-if="instance && instance.aparteante"
      :individuo_id="instance.aparteante"
      :key="`individuo-aparteante-${instance.aparteante}`"
      :ref="`individuo-aparteante-${instance.aparteante}`"
      ></individuo-aparteante>
  </div>
</template>
<script>
import Vuex from 'vuex'
import CronometroPalavra from '../components/cronometros/CronometroPalavra.vue'
import IndividuoAparteante from './IndividuoAparteante.vue'
export default {
  name: 'palavra-em-uso',
  components: {
    CronometroPalavra,
    IndividuoAparteante
  },
  data () {
    return {
      init: false,
      app: 'painelset',
      model: 'individuo',
      instance: null,
      id: null
    }
  },
  computed: {
    ...Vuex.mapGetters([
      'getIndividuoComPalavra'
    ]),
    fotografiaParlamentarUrl: function () {
      if (this.instance && this.instance.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.instance.parlamentar + '/fotografia.c96.png'
      }
      return null
    }
  },
  watch: {
    getIndividuoComPalavra: function (newVal, oldVal) {
      if (newVal !== oldVal) {
        console.log('getIndividuoComPalavra mudou', newVal, oldVal)
        this.instance = newVal
        this.initCronometro = !newVal
      }
    }
  },
  mounted () {
    console.log('PalavraEmUso mounted')
    const t = this
    t.init = true
    t.$nextTick(() => {
      t.instance = t.getIndividuoComPalavra
      if (t.instance) {
        t.id = t.instance.id
      }
    })
  },
  methods: {
    fetch (metadata) {
      const t = this
      if (metadata && metadata.hasOwnProperty('instance') && metadata.instance && metadata.instance.com_a_palavra) {
        t.instance = metadata.instance
      } else {
        t.instance = t.getIndividuoComPalavra
      }
      this
        .refreshState(metadata)
        .then((instance) => {
          if (instance && instance.com_a_palavra) {
            this.instance = instance
          } else if (instance && this.instance && instance.id === this.instance.id && !instance.com_a_palavra) {
            this.instance = null
          }
        })
    }
  }
}
</script>
<style lang="scss">
.palavraemuso-component {
  position: absolute;
  top: 2em;
  width: 66.67%;
  right: 0;
  bottom: 0;
  background-color: #222;
  display: flex;
  flex-direction: column;
  .individuo-com-a-palavra {
    display: flex;
    flex-direction: column;
    .inner-individuo {
      display: flex;
      flex-direction: row;
      align-items: stretch;
      justify-content: space-between;
    }
    .individuo-header {
      font-weight: bold;
      text-align: left;
      font-size: 1.2em;
      color: #fff;
      width: 100%;
      .name {
        background-color: #444;
        white-space: nowrap;
        margin: 0.5em 1em 0 0.5em;
        padding: 7px 14px 6px;
        min-width: 20%;
        display: inline-block;
        text-align: center;
      }
    }
    .individuo {
      flex: 1 1 0%;
    }
    .divide {
      width: 1px;
      background-color: #888;
      margin: 0;
    }
    .cronometro {
      flex: 1 1 100%;
      padding: 1em 1em 3em;
      position: relative;
      .icon-status-microfone {
        position: absolute;
        top: 0.5em;
        left: 1em;
        font-size: 3em;
        color: #ccc;
        i {
          &.fa-microphone {
            color: #4c4;
          }
          &.fa-microphone-slash {
            color: #dd1010;
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
        width: 6em;
        height: 6em;
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
@media screen and (max-width: 991.98px) {
  .palavraemuso-component {
    .individuo-com-a-palavra {
      .divide {
        width: 0;
      }
      .inner-individuo {
        flex-direction: column;
      }
      .individuo-header {
        .name {
          font-size: 1em;
          padding: 5px 10px 4px;
          margin: 0.5em 0.5em 0 0.5em;
        }
      }
      .cronometro {
        padding: 1em 1em 1.5em;
        .icon-status-microfone {
          font-size: 2em;
          top: 0.3em;
          left: 0.5em;
        }
      }
      .individuo {
        padding: 0.5em;
        .avatar {
          i {
            font-size: 3em;
          }
        }
      }
    }
    .croncard {
      .btn-group {
        flex-wrap: wrap;
        .btn-add3m, .btn-add5m, .btn-stop,  .btn-toggle {
          display: none;
        }
      }
    }
  }
}
</style>
