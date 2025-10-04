<template>
  <div :class="['individuo-base', sound_status === 0 ? 'muted' : '', individuo && individuo.com_a_palavra ? 'com-a-palavra' : '']">
    <div class="inner">
      <div class="inner-individuo" @click="$emit('individuo-com-a-palavra', individuo_id)">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user-circle fa-2x"></i>
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
        </div>
      </div>
      <div class="controls">
        <button
          v-if="individuo"
          class="btn-fone"
          :title="sound_status === 0 ? 'Ativar microfone' : 'Desativar microfone'"
           @click="sound_status = sound_status === 0 ? 1 : 0; $emit('toggle-microfone', individuo.id, sound_status)"
        >
          <i :class="sound_status === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
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
    }
  },
  data () {
    return {
      init: false,
      sound_status: this.individuo && this.individuo.sound_status ? 1 : 0,
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
  watch: {
    individuo: function (newVal, oldVal) {
      if (newVal && oldVal) {
        if (newVal.sound_status !== oldVal.sound_status) {
          this.sound_status = newVal.sound_status ? 1 : 0
        }
      }
    },
    sound_status: function (newVal, oldVal) {
      console.log('sound_status mudou', newVal, oldVal)
      if (!this.send_individual_updates) {
        this.send_individual_updates = true
        console.log('send_individual_updates is false, not sending update')
        return
      }
      this.utils.getModelAction('painelset', 'individuo', this.individuo_id, 'toggle_microfone', `&sound_status=${newVal ? 'on' : 'off'}&com_a_palavra=${this.individuo && this.individuo.com_a_palavra && newVal ? 1 : 0}`)
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
  .avatar {
    img {
      width: 2em;
      height: 2em;
      object-fit: cover;
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
    border: 2px solid #0364d3;
    .inner-individuo, .controls {
      background: #57bbe9;
      opacity: 1 !important;
      font-weight: bold;
    }
    .inner-individuo {
      cursor: default;
      font-size: 1.2em;
      border-color: transparent;
    }
  }
}
</style>
