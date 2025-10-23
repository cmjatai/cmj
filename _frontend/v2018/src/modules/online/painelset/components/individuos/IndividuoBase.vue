<template>
  <div :class="[
    'individuo-base',
    individuo && individuo.status_microfone ? '' :  'muted',
    individuo && individuo.parlamentar ? 'parlamentar' : '',
    individuo && individuo.com_a_palavra ? 'com-a-palavra' : (individuo && individuo.microfone_sempre_ativo ? 'always-on' : 'active'),
    individuo && individuo.aparteado ? 'aparteante' : ''
    ]">
    <div class="inner">
      <div class="inner-individuo" @dblclick.stop="dblclickIndividuo($event)" @click.prevent="clickIndividuo($event)">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user"></i>
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
          <small>{{ individuo ? `(${individuo.canal})` : '' }}</small>
        </div>
      </div>
      <div class="controls">
        <button
          v-if="individuo"
          class="btn-fone"
          :title="individuo && individuo.status_microfone ? 'Ativar microfone' : 'Desativar microfone'"
           @click="toggleMicrofone()"
        >
          <i :class="individuo && individuo.status_microfone ? 'fas fa-2x fa-microphone' : 'fas fa-2x fa-microphone-slash'"></i>
        </button>
        <button
          v-if="false && individuo"
          class="btn-control"
        >
          <i class="fas fa-cog"></i>
        </button>
      </div>
    </div>
  </div>
</template>
<script>
import { EventBus } from '@/event-bus'

export default {
  name: 'individuo-base',
  props: {
    individuo_id: {
      type: Number,
      required: true
    },
    default_timer: {
      type: Number,
      required: false,
      default: 300 // seconds
    },
    default_timer_aparteante: {
      type: Number,
      required: false,
      default: 60 // seconds
    }
  },
  data () {
    return {
      click_timeout: null
    }
  },
  computed: {
    individuoComPalavra: {
      get () {
        if (this.data_cache?.painelset_individuo) {
          return Object.values(this.data_cache.painelset_individuo).find(i => i.com_a_palavra && i.evento === this.individuo.evento) || null
        }
        return null
      }
    },
    individuo: function () {
      if (this.data_cache?.painelset_individuo && this.individuo_id) {
        return this.data_cache.painelset_individuo[this.individuo_id] || null
      }
      return null
    },
    fotografiaParlamentarUrl: function () {
      if (this.individuo?.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.individuo.parlamentar + '/fotografia.c96.png'
      }
      return ''
    }
  },
  mounted () {
    console.debug('Individuo Base mounted', this.individuo_id)
    EventBus.$on('toggle-microfone-individuo', (individuo_id) => {
      if (individuo_id === this.individuo_id) {
        this.toggleMicrofone()
      }
    })
  },
  methods: {
    toggleMicrofone: function () {
      this.sendUpdate(
        'toggle_microfone',
        [
          `status_microfone=${!this.individuo?.status_microfone ? 'on' : 'off'}`,
          `default_timer=${this.default_timer}`,
          `com_a_palavra=${this.individuo?.com_a_palavra ? 1 : 0}`
        ]
      )
    },
    clickIndividuo: function (event) {
      const t = this
      clearTimeout(t.click_timeout)
      t.click_timeout = setTimeout(() => {
        if (t.individuo?.com_a_palavra || !t.individuoComPalavra) {
          if (t.individuo === t.individuoComPalavra) {
            t.sendMessage({ alert: 'error', message: 'A palavra já está sendo utilizada por este indivíduo.', time: 7 })
            return
          }
          this.sendMessage({ alert: 'error', message: 'A palavra não está sendo utilizada. Não é possível fazer aparte.', time: 7 })
          return
        }
        t.sendUpdate(
          'toggle_aparteante',
          [
            `aparteante_status=${!t.individuo.aparteado ? 1 : 0}`,
            `default_timer=${t.default_timer_aparteante || 60}`
          ]
        )
      }, 600)
    },
    dblclickIndividuo: function (event) {
      clearTimeout(this.click_timeout)
      this.sendUpdate(
        'toggle_microfone',
        [
          `status_microfone=${this.individuo?.status_microfone || !this.individuo?.com_a_palavra ? 'on' : 'off'}`,
          `default_timer=${this.default_timer}`,
          `com_a_palavra=${!this.individuo?.com_a_palavra ? 1 : 0}`
        ]
      )
    },
    sendUpdate (action, query_params) {
      return this
        .utils.getModelAction(
          'painelset', 'individuo', this.individuo_id, action,
          query_params.join('&')
        )
        .then(response => {
          console.debug(this.individuo_id, action, response)
        })
        .catch(error => {
          console.error(this.individuo_id, action, error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar indivíduo: ' + error.response.data, time: 5 })
        })
    }
  }
}
</script>
<style lang="scss">
.individuo-base {
  display: flex;
  align-self: stretch;
  justify-content: stretch;
  border-bottom: 1px solid white;
  position: relative;
  &:last-child {
  border-bottom: 0px;
  }
  .inner {
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: absolute;
  }
  .inner-individuo, .controls {
    display: flex;
    background: #ddffdd;
    align-items: stretch;
    flex: 1 1 auto;
    padding: 0;
  }
  .avatar {
    border-radius: 0;
    img {
      border-radius: 0;
      height: 100%;
    }
    i {
      margin: 0 10px 0 20px;
      font-size: 2em;
    }
  }
  .inner-individuo {
    cursor: pointer;
    align-items: center;
    gap: 10px;
    border-right: 1px solid white;
    .name {
      flex: 1 1 100%;
      small {
        opacity: 0.5;
      }
    }
  }

  .controls {
    flex: 0 1 0;
  }
  .btn-fone, .btn-control {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 5em;
    font-size: 0.7rem;
    border: 0;
    background: transparent;
  }
  .btn-control {
    width: auto;
  }
  .fa-microphone {
    color: green;
    opacity: 0.6;
  }
  .fa-microphone-slash {
    opacity: 0.4;
  }
  &:hover {
    .inner-individuo, .controls {
      background: #bbffbb;
    }
  }
  &.muted {
    .inner-individuo, .controls {
      background: #ffdddd;
      opacity: 0.8;
    }
    &:hover {
      .inner-individuo, .controls {
        background: #ffcccc;
        opacity: 1;
      }
    }
  }
  &.com-a-palavra {
    border-left: 0;
    border-right: 0;
    .inner-individuo, .controls {
      background: linear-gradient(to right, #0364d3, #0253a8);
      opacity: 1 !important;
      font-weight: bold;
      color: white;
      .fa-microphone {
        color: white;
        opacity: 1;
      }
    }
    .inner-individuo {
      font-size: 1.2em;
      border-color: transparent;
    }
  }
  &.aparteante {
    margin-left: 10%;
    .inner-individuo, .controls {
      background: linear-gradient(to right, #d3a103, #a87f02);
      opacity: 1 !important;
      font-weight: bold;
      color: black;
      .fa-microphone {
        color: black;
        opacity: 1;
      }
    }
    .inner-individuo {
      font-size: 1.2em;
      border-color: transparent;
    }
  }
  &.always-on:not(.muted):not(.com-a-palavra):not(.aparteante) {
    .inner-individuo, .controls {
      background: #7ee57e;
      opacity: 1 !important;
    }
  }
}
@media screen and (max-width: 991.98px) {
  .individuo-base {
    .inner-individuo {
      gap: 0;
    }
    &:not(.parlamentar) {
      i {
        margin: 0;
        padding: 0 5px;
      }
    }
    &.parlamentar {
      .avatar {
        width: 100%;
        text-align: center;
      }
      .name {
        display: none;
      }
    }
  }
}
</style>
