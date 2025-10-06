<template>
  <div :class="['individuo-base', status_microfone === 0 ? 'muted' : '', individuo && individuo.com_a_palavra ? 'com-a-palavra' : (individuo.microfone_sempre_ativo ? 'always-on' : 'active')]">
    <div class="inner">
      <div class="inner-individuo" @dblclick="dblclickIndividuo($event)">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user"></i>
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
        </div>
      </div>
      <div class="controls">
        <button
          v-if="individuo"
          class="btn-fone"
          :title="status_microfone === 0 ? 'Ativar microfone' : 'Desativar microfone'"
           @click="status_microfone = status_microfone === 0 ? 1 : 0; $emit('toggle-microfone', individuo.id, status_microfone)"
        >
          <i :class="status_microfone === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
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
    }
  },
  data () {
    return {
      init: false,
      status_microfone: this.individuo && this.individuo.status_microfone ? 1 : 0,
      com_a_palavra: this.individuo && this.individuo.com_a_palavra,
      // To avoid infinite loop when changing status_microfone from prop change and watcher on status_microfone
      send_individual_updates: true
    }
  },
  computed: {
    fotografiaParlamentarUrl: function () {
      if (this.individuo && this.individuo.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.individuo.parlamentar + '/fotografia.c96.png'
      }
      return null
    }
  },
  mounted () {
    console.log(this.individuo_id, 'IndividuoBase mounted', this.individuo)
    const t = this
    t.init = true
    this.refreshState({
      app: 'painelset',
      model: 'cronometro',
      id: this.individuo.cronometro
    })
  },
  watch: {
    individuo: function (newVal, oldVal) {
      console.log(this.individuo_id, 'individuo mudou', newVal, oldVal)
      if (newVal && oldVal) {
        if (newVal.status_microfone !== oldVal.status_microfone) {
          this.status_microfone = newVal.status_microfone ? 1 : 0
        }
        if (newVal.com_a_palavra !== oldVal.com_a_palavra) {
          this.com_a_palavra = newVal.com_a_palavra
        }
      }
      this.refreshState({
        app: 'painelset',
        model: 'cronometro',
        id: this.individuo.cronometro
      })
    },
    com_a_palavra: function (newVal, oldVal) {
      console.log(this.individuo_id, 'com_a_palavra mudou', newVal, oldVal)
      if (!this.send_individual_updates) {
        this.send_individual_updates = true
        console.log('send_individual_updates is false, not sending update')
        return
      }
      this.utils.getModelAction(
        'painelset', 'individuo', this.individuo_id, 'toggle_microfone',
        `&status_microfone=${this.status_microfone ? 'on' : 'off'}&com_a_palavra=${newVal ? 1 : 0}&default_timer=${this.default_timer}`)
        .then(response => {
          console.log(this.individuo_id, 'com_a_palavra, toggle_microfone response', response)
        })
        .catch(error => {
          console.error(this.individuo_id, 'com_a_palavra, toggle_microfone error', error)
        })
    },
    status_microfone: function (newVal, oldVal) {
      console.log(this.individuo_id, 'status_microfone mudou', newVal, oldVal)
      if (!this.send_individual_updates) {
        this.send_individual_updates = true
        console.log('send_individual_updates is false, not sending update')
        return
      }
      if (this.individuo && this.individuo.microfone_sempre_ativo && newVal === 0) {
        console.log('individuo.microfone_sempre_ativo is true, not allowing to turn off microphone')
        this.status_microfone = 1
        return
      }
      this.utils.getModelAction(
        'painelset', 'individuo', this.individuo_id, 'toggle_microfone',
        `&status_microfone=${newVal ? 'on' : 'off'}&com_a_palavra=${this.individuo && this.individuo.com_a_palavra && newVal ? 1 : 0}&default_timer=${this.default_timer}`)
        .then(response => {
          console.log(this.individuo_id, 'com_a_palavra, toggle_microfone response', response)
        })
        .catch(error => {
          console.error(this.individuo_id, 'com_a_palavra, toggle_microfone error', error)
        })
    }
  },
  methods: {
    dblclickIndividuo: function (event) {
      if (!this.individuo) {
        return
      }
      console.log(event)
      this.$emit('toggle-com-a-palavra', this.individuo.id)
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
  &.always-on:not(.muted):not(.com-a-palavra) {
    .inner-individuo, .controls {
      background: #7ee57e;
      opacity: 1 !important;
    }
    .inner-individuo {
    }
  }
}
</style>
