<template>
  <div :class="[
    'individuo-base', status_microfone ? '' :  'muted',
    instance && instance.parlamentar ? 'parlamentar' : '',
    com_a_palavra ? 'com-a-palavra' : (microfone_sempre_ativo ? 'always-on' : 'active'),
    aparteante ? 'aparteante' : ''
    ]">
    <div class="inner">
      <div class="inner-individuo" @dblclick.stop="dblclickIndividuo($event)" @click.prevent="clickIndividuo($event)">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user"></i>
        </div>
        <div class="name">
          {{ instance ? instance.name : 'Carregando indivíduo...' }}
          <small>{{ instance ? `(${instance.canal})` : '' }}</small>
        </div>
      </div>
      <div class="controls">
        <button
          v-if="instance"
          class="btn-fone"
          :title="status_microfone ? 'Ativar microfone' : 'Desativar microfone'"
           @click="toggleMicrofone()"
        >
          <i :class="status_microfone ? 'fas fa-2x fa-microphone' : 'fas fa-2x fa-microphone-slash'"></i>
        </button>
        <button
          v-if="false && instance"
          class="btn-control"
        >
          <i class="fas fa-cog"></i>
        </button>
      </div>
    </div>
  </div>
</template>
<script>
import Vuex from 'vuex'
export default {
  name: 'individuo-base',
  props: {
    individuo_id: {
      type: Number,
      required: true
    },
    individuo: {
      type: Object,
      required: false,
      default: null
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
      id: this.individuo_id,
      instance: null,
      app: 'painelset',
      model: 'individuo',
      init: false,
      send_individual_updates: true,
      click_timeout: null
    }
  },
  computed: {
    ...Vuex.mapGetters([
      'getIndividuoComPalavra'
    ]),
    status_microfone: function () {
      return this.instance && this.instance.status_microfone
    },
    microfone_sempre_ativo: function () {
      return this.instance && this.instance.microfone_sempre_ativo
    },
    com_a_palavra: function () {
      return this.instance && this.instance.com_a_palavra
    },
    aparteante: function () {
      return this.instance && this.instance.aparteado
    },
    fotografiaParlamentarUrl: function () {
      if (this.instance && this.instance.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.instance.parlamentar + '/fotografia.c96.png'
      }
      return ''
    }
  },
  mounted () {
    console.log('Individuo Base mounted', this.individuo_id)
    const t = this
    t.init = true
    t.$nextTick(() => {
      if (t.individuo) {
        t.instance = t.individuo
        if (t.instance && !t.instance.com_a_palavra && !t.instance.aparteado) {
          t.utils.getModelAction(t.app, t.model, t.individuo_id, 'force_stop_cronometro')
        }
      } else {
        t.fetch()
      }
    })
  },
  methods: {
    toggleMicrofone: function () {
      this.sendUpdate(
        'toggle_microfone',
        [
          `status_microfone=${!this.status_microfone ? 'on' : 'off'}`,
          `default_timer=${this.default_timer}`,
          `com_a_palavra=${this.com_a_palavra ? 1 : 0}`
        ]
      )
    },
    clickIndividuo: function (event) {
      const t = this
      clearTimeout(t.click_timeout)
      t.click_timeout = setTimeout(() => {
        if (t.instance.com_a_palavra || !t.getIndividuoComPalavra) {
          if (t.instance === t.getIndividuoComPalavra) {
            t.sendMessage({ alert: 'error', message: 'A palavra já está sendo utilizada por este indivíduo.', time: 7 })
            return
          }
          this.sendMessage({ alert: 'error', message: 'A palavra não está sendo utilizada. Não é possível fazer aparte.', time: 7 })
          return
        }
        t.sendUpdate(
          'toggle_aparteante',
          [
            `aparteante_status=${!t.aparteante ? 1 : 0}`,
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
          `status_microfone=${this.status_microfone || !this.com_a_palavra ? 'on' : 'off'}`,
          `default_timer=${this.default_timer}`,
          `com_a_palavra=${!this.com_a_palavra ? 1 : 0}`
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
          console.log(this.individuo_id, action, response)
        })
        .catch(error => {
          console.error(this.individuo_id, action, error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar indivíduo: ' + error.response.data, time: 5 })
        })
    },
    fetch (metadata) {
      const t = this
      if (!metadata &&
        metadata.hasOwnProperty('action') &&
        metadata.action === 'post_delete' &&
        metadata.model === 'individuo') {
        t.instance = null
        return
      }
      if (metadata.hasOwnProperty('instance') && metadata.instance && metadata.instance.id === t.individuo_id) {
        t.instance = metadata.instance
      }
      t
        .refreshState(metadata)
        .then((individuo) => {
          if (individuo && individuo.id === t.individuo_id) {
            t.instance = individuo
          }
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
