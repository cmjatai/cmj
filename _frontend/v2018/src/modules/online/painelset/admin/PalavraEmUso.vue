<template>
  <div class="palavraemuso-component">
    <div :class="['individuo-com-a-palavra', ]"
      v-if="individuo"
      :key="`individuo-com-a-palavra-${individuo.id}`"
      :ref="`individuo-com-a-palavra-${individuo.id}`">
      <div class="inner-individuo">
        <div class="individuo-header">
          <div class="name">
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
        <div class="cronometro">
          <cronometro-palavra
          :key="`cronometro-com-a-palavra-${individuo.cronometro}`"
          :ref="`cronometro-com-a-palavra-${individuo.cronometro}`"
          :cronometro_id="individuo.cronometro"
          ></cronometro-palavra>
          <div class="icon-status-microfone" @click="toggleMicrofone">
            <i v-if="individuo && individuo.status_microfone" class="fas fa-microphone"></i>
            <i v-else class="fas fa-microphone-slash"></i>
          </div>
        </div>
      </div>
    </div>
    <individuo-aparteante
      v-if="individuo && individuo.aparteante"
      :individuo_id="individuo.aparteante"
      :key="`individuo-aparteante-${individuo.aparteante}`"
      :ref="`individuo-aparteante-${individuo.aparteante}`"
      ></individuo-aparteante>
  </div>
</template>
<script>
import CronometroPalavra from './CronometroPalavra.vue'
import IndividuoAparteante from './IndividuoAparteante.vue'
import { EventBus } from '@/event-bus'

export default {
  name: 'palavra-em-uso',
  components: {
    CronometroPalavra,
    IndividuoAparteante
  },
  props: {
    evento: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
    }
  },
  computed: {
    individuo: {
      get () {
        if (this.evento && this.data_cache?.painelset_individuo) {
          return Object.values(this.data_cache.painelset_individuo).find(i => i.com_a_palavra && i.evento === this.evento.id) || null
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
  },
  methods: {
    toggleMicrofone: function () {
      EventBus.$emit('toggle-microfone-individuo', this.individuo.id)
    }
  }
}
</script>
<style lang="scss">
.palavraemuso-component {
  position: absolute;
  width: 66.67%;
  top: 0;
  right: 0;
  bottom: 0;
  background-color: #222;
  display: flex;
  flex-direction: column;
  z-index: 0;
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
        right: 1em;
        font-size: 3em;
        color: #ccc;
        cursor: pointer;
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
    width: 100%;
    top: 2.1em;
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
          right: 0.5em;
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
