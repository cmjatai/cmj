<template>
  <div class="popover-palavra"
    v-if="individuos"
      @touchstart="touching = true"
      @touchmove="movePopover($event)"
      @touchend="touching = false"
      @mouseup="touching = false"
      @mousemove="movePopover($event)"
      @mousedown="touching = true"
    >
    <div :class="['popover-individuo', individuo.com_a_palavra ? 'com_a_palavra': 'aparteante']" v-for="individuo in individuos" :key="`popover-individuo-${individuo.id}`">
      <div class="popover-header">
        <div class="arrow"></div>
        <h3 class="popover-title" v-if="individuo.com_a_palavra">Com a palavra</h3>
        <h3 class="popover-title" v-if="individuo.aparteado">Em aparte</h3>
      </div>
      <div class="popover-body">
        <div v-if="individuo" class="individuo-info">
          <div class="info">
            <div class="name">{{ individuo.nome }}</div>
            <div class="timer mt-1" v-if="individuo.cronometro">
              <cronometro-base
                :cronometro_id="individuo.cronometro"
                :key="`cronometro-popover-${individuo.cronometro}`"
                :ref="`cronometro-popover-${individuo.cronometro}`"
                css_class_controls="d-none"
                css_class="cron-popover-palavra"
                :display_initial="'remaining'"
                :display_format="'mm:ss'"
                :display_size="'2em'"
                :controls="[]"
              ></cronometro-base>
            </div>
          </div>
          <div class="foto me-2"
            v-if="individuo.parlamentar"
            :style="{ backgroundImage: 'url(' + fotografiaParlamentarUrl(individuo.parlamentar) + ')' }"></div>
          <div class="foto me-2" v-else>
            <i class="fas fa-user"></i>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import CronometroBase from '../../components/cronometros/CronometroBase.vue'

export default {
  name: 'popover-palavra',
  components: {
    CronometroBase
  },
  data () {
    return {
      app: [
        'painelset'
      ],
      model: [
        'individuo',
        'cronometro'
      ],
      touching: false,
      moving: false,
      individuo_com_a_palavra: null,
      cronometro_com_a_palavra: null,
      individuo_aparteante: null,
      cronometro_aparteante: null
    }
  },
  computed: {
    individuos: function () {
      const individuos = []
      if (this.individuo_aparteante) {
        individuos.push(this.individuo_aparteante)
      }
      if (this.individuo_com_a_palavra) {
        individuos.push(this.individuo_com_a_palavra)
      }
      return individuos
    }
  },
  methods: {
    fotografiaParlamentarUrl (parlamentar) {
      if (parlamentar) {
        return '/api/parlamentares/parlamentar/' + parlamentar + '/fotografia.c96.png'
      }
      return null
    },
    fetch (metadata) {
      const t = this
      return t
        .refreshState(metadata)
        .then((obj) => {
          if (metadata.model === 'individuo') {
            if (obj && obj.com_a_palavra) {
              if (obj.aparteado !== t.individuo_aparteante?.id) {
                t.individuo_aparteante = null
              }
              t.individuo_com_a_palavra = obj
              return obj
            }
            if (obj && obj.aparteado) {
              t.individuo_aparteante = obj
            }
            if (obj && !obj.com_a_palavra && !obj.aparteado && t.individuo_com_a_palavra?.id === obj.id) {
              t.individuo_com_a_palavra = null
            }
            if (obj && !obj.com_a_palavra && !obj.aparteado && t.individuo_aparteante?.id === obj.id) {
              t.individuo_aparteante = null
            }
          }
          return obj
        })
        .catch((err) => {
          console.error('Erro ao atualizar o estado', err)
          throw err
        })
    },
    movePopover (event) {
      event.preventDefault()
      if (!this.touching) return
      console.log('movePopover', event)
      const popover = event.target.closest('.popover-palavra')
      const offsetX = 20
      const offsetY = 20

      let touches = event.touches
      if (touches !== undefined) {
        touches = event.touches || event.originalEvent.touches
        if (touches && touches.length) {
          event = touches[0]
        }
      }

      let right = window.innerWidth - event.clientX - offsetX - popover.offsetWidth / 2
      let bottom = window.innerHeight - event.clientY - offsetY - popover.offsetHeight / 2

      if (right < -popover.offsetWidth / 2) right = -popover.offsetWidth / 2
      if (bottom < -popover.offsetHeight / 2) bottom = -popover.offsetHeight / 2
      if (right + popover.offsetWidth > window.innerWidth) {
        right = window.innerWidth - popover.offsetWidth
      }
      if (bottom + popover.offsetHeight > window.innerHeight) {
        bottom = window.innerHeight - popover.offsetHeight
      }

      popover.style.right = `${right}px`
      popover.style.bottom = `${bottom}px`
    }
  }
}
</script>

<style lang="scss">
.popover-palavra {
  user-select: none;
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1050;
  width: auto;
  opacity: 0.4;
  text-align: right;
  &:hover {
    opacity: 1.0;
  }
  .arrow {
    position: absolute;
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-top: 10px solid #333;
    bottom: -10px;
    right: 20px;
  }
  .popover-header {
    background-color: #333;
    color: white;
    padding: 0.1em 0.5em;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    border-bottom: 1px solid #444;
    position: relative;
    .popover-title {
      margin: 0;
      font-size: 1.1em;
      font-weight: bold;
    }
  }
  .popover-body {
    background-color: #222;
    padding: 10px;
    border-bottom-left-radius: 3px;
    border-bottom-right-radius: 3px;
    border: 1px solid #222;
    border-top: 0;
    .cron-popover-palavra {
      font-size: 1em;
      font-weight: bold;
      color: #007bff;
    }
  }
  .popover-individuo {
    border-radius: 10px;
    overflow: hidden;
    &.aparteante {
      margin-bottom: 1px;
      zoom: 0.7;
      display: inline-block;
      margin-right: 0.6em;
      .popover-body {
        background-color: #4e2f01;
      }
      .popover-header {
        background-color: #775201;
      }
    }
    .individuo-info {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1em;
      .info {
        display: flex;
        flex-direction: column;
      }
      .foto {
        width: 2em;
        height: 2em;
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        background-color: #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2em;
        color: white;
      }
      .info {
        .name {
          font-weight: bold;
          font-size: 1.1em;
          small {
            font-weight: normal;
            font-size: 0.9em;
            margin-left: 5px;
          }
        }
        .role {
          font-size: 0.9em;
          color: #666;
        }
        .timer {
          font-size: 0.9em;
          color: #007bff;
          font-weight: bold;
          .cron-popover-palavra {
            font-size: 1em;
            font-weight: bold;
            color: #007bff;
            .croncard {
              background-color: transparent;
              padding: 0;
              border: 0;
              box-shadow: none;
            }
          }
        }
      }
    }
  }
}
</style>
