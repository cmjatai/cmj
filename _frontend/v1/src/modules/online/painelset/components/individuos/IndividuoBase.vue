<template>
  <div :class="['individuo-base', sound_status === 0 ? 'muted' : '']">
    <div class="inner">
      <div class="inner-individuo" @click="sound_status = sound_status === 0 ? 1 : 0; $emit('toggle-microfone', individuo.id, sound_status)">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user-circle fa-2x"></i>
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
        </div>
        <button
          v-if="individuo"
          class="btn-fone"
          :title="sound_status === 0 ? 'Ativar microfone' : 'Desativar microfone'"
        >
          <i :class="sound_status === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
        </button>
      </div>
      <div class="controls">
        <button
          v-if="individuo"
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
    }
  },
  data () {
    return {
      init: false,
      sound_status: 0,
      send_individual_updates: true
    }
  },
  computed: {
    fotografiaParlamentarUrl: function () {
      if (this.individuo && this.individuo.parlamentar) {
        return '/api/parlamentares/parlamentar/' + this.individuo.parlamentar + '/fotografia.c48.png'
      }
      return null
    }
  },
  watch: {
    sound_status: function (newVal, oldVal) {
      console.log('sound_status mudou', newVal, oldVal)
      if (!this.send_individual_updates) {
        this.send_individual_updates = true
        console.log('send_individual_updates is false, not sending update')
        return
      }
      this.utils.getModelAction('painelset', 'individuo', this.individuo_id, 'toggle_microfone', `&sound_status=${newVal ? 'on' : 'off'}`)
        .then(response => {
          console.log('toggle_microfone response', response)
        })
        .catch(error => {
          console.error('toggle_microfone error', error)
        })
    }
  }
}
</script>
<style lang="scss">
.individuo-base {
  border-bottom: 1px solid white;
  &:last-child {
  border-bottom: 0px;
  }
  .inner {
    display: flex;
    align-items: stretch;
    justify-content: space-between;
  }
  .inner-individuo, .controls {
    display: flex;
    background: #ddffdd;
    align-items: stretch;
    flex: 1 1 auto;
    padding: 5px 10px;
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
}
</style>
