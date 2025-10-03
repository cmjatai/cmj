<template>
  <div :class="['individuo-base', sound_status === 0 ? 'muted' : '']">
    <div class="inner"  @click="sound_status = sound_status === 0 ? 1 : 0; $emit('toggle-microfone', individuo.id, sound_status)">
      <div class="inner-individuo">
        <div class="avatar">
          <img v-if="fotografiaParlamentarUrl" :src="fotografiaParlamentarUrl" alt="Foto do parlamentar"/>
          <i v-else class="fas fa-user-circle fa-2x"></i>
        </div>
        <div class="name">
          {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
        </div>
      </div>
      <div class="controls">
        <button v-if="individuo" :title="sound_status === 0 ? 'Ativar microfone' : 'Desativar microfone'" class="btn-microfone">
          <i :class="sound_status === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
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
      sound_status: 0
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
  padding: 5px;
  background: #ddffdd;
  &:not(:last-child) {
    border-bottom: 1px solid #cccc;
  }
  &:hover {
    background: #ccffcc;
  }
  &.muted {
    background: #fffafa;
    opacity: 0.6;
    .fa-microphone-slash {
      color: red;
    }
    &:hover {
      background: #fff0f0;
    }
  }
  .fa-microphone {
    color: green;
  }
  .fa-microphone-slash {
    opacity: 0.4;
  }
  .btn-microfone {
    width: 4em;
    font-size: 0.7rem;
    justify-content: center;
    display: flex;
    border: 0;
    background: transparent;
  }
  .inner {
    display: flex;
    align-items: center;
    .inner-individuo {
      flex-grow: 1;
      display: flex;
      align-items: center;
      .avatar {
        margin-right: 5px;
      }
    }
    .name {
      font-weight: bold;
    }
  }
}
</style>
