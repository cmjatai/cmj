<template>
  <div class="individuo-aparteante-component">
    <div :class="['individuo-aparteante', ]"
      v-if="individuo"
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
import CronometroPalavra from './CronometroPalavra.vue'
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
    }
  },
  computed: {
    individuo: {
      get () {
        if (this.individuo_id && this.data_cache?.painelset_individuo) {
          return this.data_cache.painelset_individuo[this.individuo_id] || null
        }
        return null
      }
    },
    fotografiaParlamentarUrl: function () {
      if (this.individuo && this.individuo.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.individuo.parlamentar + '/fotografia.c96.png'
      }
      return null
    }
  }
}
</script>
<style lang="scss">
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
@media screen and (max-width: 991.98px) {
  .individuo-aparteante-component {
    .individuo-aparteante {
      border-top: 1px solid #888;
      margin-top: 1em;
      align-items: flex-end;
      margin-left: 0;
      .individuo-header {
        .name {
          display: flex;
          flex-direction: column;
          text-align: right;
          font-size: 1em;
          padding: 5px 10px 4px;
          margin: 0.5em 0.5em 0 0.5em;
          strong {
            display: inline-block;
            width: 100%;
          }
        }
      }
      .inner-individuo {
        flex-direction: column;
      }
      .cronometro {
        padding: 0.5em;
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
  }
}
</style>
