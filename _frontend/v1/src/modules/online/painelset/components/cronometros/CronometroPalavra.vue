<template>
  <div class="cronometro-palavra">
    <cronometro-base
      :cronometro_id="cronometro_id"
      :key="`cronometro-palavra-${cronometro_id}`"
      :ref="`cronometro-palavra-${cronometro_id}`"
      css_class_controls="visible"
      css_class="cron-palavra"
      :display_initial="'remaining'"
      :display_format="'mm:ss'"
      :display_size="'4em'"
      :auto_start="auto_start"
      :controls="controls"
    ></cronometro-base>
  </div>
</template>
<script>
import CronometroBase from './CronometroBase.vue'

export default {
  name: 'cronometro-palavra',
  components: {
    CronometroBase
  },
  props: {
    cronometro_id: {
      type: Number,
      required: true
    },
    controls: {
      type: Array,
      required: false,
      default: function () {
        return [
          'start',
          'pause',
          'resume',
          'stop',
          'add30s',
          'add1m',
          'add3m',
          'add5m',
          'toggleDisplay'
        ]
      }
    }
  },
  data () {
    return {
      auto_start: true
    }
  },
  mounted () {
    console.log('CronometroPalavra mounted', this.cronometro_id)
    const t = this
    // t.fetch()
    t.$nextTick(() => {
      t.auto_start = false
    })
  },
  beforeDestroy () {
    console.log('CronometroPalavra beforeDestroy', this.cronometro_id)
  },
  methods: {
  }
}
</script>
<style lang="scss">
@media screen and (min-width: 992px) {
  .cronometro-palavra {
    height: 100%;
    .cronometro-component {
      &.cron-palavra {
        color: white;
        height: 100%;
      }
      .croncard {
        background-color: #222;
        height: 100%;
        justify-content: space-between;
        padding: 0;
      }
      .controls {
        &.visible {
          visibility: visible !important;
          width: 100%;
          .btn-group {
            width: 100%;
            margin-top: 1.5em;

            .btn {
              justify-content: center;
              padding: 0.5em 0;
              font-size: 1em;
              font-weight: bold;
              &:hover {
                box-shadow: 0px 0px 10px #000;
              }
            }
            .btn-outline-dark {
              color: white;
              border-color: #444;
              background-image: linear-gradient(to bottom, #444, #333);
              flex: 1 2 auto;
              &:hover {
                background-color: #444;
                border-color: #777
              }
              &.btn-negative {
                background-image: linear-gradient(to bottom, #772222, #442222);
                flex: 0 1 0;
                padding-left: 1em;
                padding-right: 1.3em;
                border-color: #772222;
                &:hover {
                  background-color: #662222;
                  border-color: #aa4444;
                }
              }
            }
          }
        }
      }
    }
  }
}
</style>
