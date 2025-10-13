<template>
  <div class="painelset-admin">
    <div class="container-grid">
      <div class="row header">
        <div class="col">
          <div class="titulo-evento">
            {{ evento ? evento.name : 'Carregando evento...' }}
            <small>
              {{ datahora_prevista_real[0] }} - {{ datahora_prevista_real[1] }} {{ datahora_prevista_real[2] }}
            </small>
          </div>
        </div>
        <div class="col-auto">
          <cronometro-base
            v-if="cronometro"
            :cronometro_id="cronometro.id"
            css_class_controls="hover"
            css_class="cronometro-global"
            :controls="['start', 'pause', 'resume', 'toggleDisplay']"
            @cronometro_start="startEvento()"
            @cronometro_pause="pauseEvento()"
            @cronometro_resume="resumeEvento()"
            ></cronometro-base>
        </div>
      </div>
      <div class="row">
        <div class="col-4 container-individuos">
          <individuo-list v-if="evento" :evento="evento" :ref="'individuoList'" :pause_parent_on_start="cronometro && cronometro.pause_parent_on_start"></individuo-list>
        </div>
        <div class="col-8 container-controls">
          <palavra-em-uso v-if="evento" :evento="evento" :ref="'palavraEmUso'"></palavra-em-uso>
        </div>
      </div>
    </div>
    <div class="disabled" v-if="cronometro && cronometro.state !== 'running'">
      <div class="overlay-paused">
        <div class="text-paused">
          <div v-if="cronometro && cronometro.state === 'paused'">
            EVENTO EM SUSPENSÃO
          </div>
          <div v-else-if="cronometro && cronometro.state === 'stopped'">EVENTO NÃO INICIADO</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CronometroBase from '../components/cronometros/CronometroBase.vue'
import IndividuoList from './IndividuoList.vue'
import PalavraEmUso from './PalavraEmUso.vue'
export default {
  name: 'painelset-admin',
  components: {
    CronometroBase,
    IndividuoList,
    PalavraEmUso
  },
  data () {
    return {
      evento_id: Number(this.$route.params.id),
      finished: false
    }
  },
  watch: {
    'evento': {
      handler (newVal) {
        if (!this.finished && newVal && newVal.end_real) {
          this.finished = true
          this.sendMessage({ alert: 'danger', message: 'Evento já finalizado. Você pode copiá-lo para gerar um novo evento.', time: 10 })
          this.$router.push({ name: 'painelset_evento_list_link' })
        }
      },
      immediate: true
    }
  },
  computed: {
    evento: function () {
      return this.data_cache['painelset_evento'] ? this.data_cache['painelset_evento'][this.evento_id] : null
    },
    cronometro: function () {
      return this.evento && this.evento.cronometro ? this.data_cache['painelset_cronometro'] ? this.data_cache['painelset_cronometro'][this.evento.cronometro] : null : null
    },
    datahora_prevista_real: function () {
      if (this.evento && !this.evento.start_real) {
        const dt = new Date(this.evento.start_previsto)
        return ['Início previsto', dt.toLocaleDateString(), dt.toLocaleTimeString()]
      } else if (this.evento && this.evento.start_real) {
        const dt = new Date(this.evento.start_real)
        return ['Iniciado em', dt.toLocaleDateString(), dt.toLocaleTimeString()]
      }
      return ['Data e hora não definidas', '', '']
    }
  },
  mounted: function () {
    this.$nextTick(() => {
      this.utils.hasPermission('painelset.change_evento')
        .then(hasPermission => {
          this.fetchSync({
            app: 'painelset',
            model: 'evento',
            id: this.evento_id
          })
          this.fetchSync({
            app: 'painelset',
            model: 'cronometro',
            id: this.evento?.cronometro
          })
        })
        .catch(() => {
          this.$router.push({ name: 'online_index_link' })
          this.sendMessage({ alert: 'danger', message: 'Você não tem permissão para acessar esta página.', time: 5 })
        })
    })
  },
  methods: {
    resumeEvento () {
      this.$refs.individuoList.status_microfone = 0
      this.$refs.individuoList.toggleAllMicrofones()
    },
    startEvento () {
      this.utils.getModelAction('painelset', 'evento', this.evento.id, 'start')
        .then(response => {
          console.log('start response', response)
        })
        .catch(error => {
          console.error('start error', error)
        })
    },
    pauseEvento () {
      this.$refs.individuoList.status_microfone = 1
      this.$refs.individuoList.toggleAllMicrofones(false)
    }
  }
}
</script>

<style lang="scss">
.painelset-admin {
  $px: 0px;
  line-height: 1;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #222;
  .container-grid {
    padding: 0 $px;
    height: 100%;
  }
  .row {
    position: relative;
    align-items: stretch;
    margin-left: -$px;
    margin-right: -$px;
    padding-top: $px;
    &:first-child {
      height: 3.4em;
    }
    &:last-child {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      top: 3.4em;
    }
    div[class^=col] {
      position: static;
      padding-left: $px;
      padding-right: $px;
      &:not(:first-child) {
        padding-left: $px / 2;
      }
      &:not(:last-child) {
        padding-right: $px / 2;
      }
    }
    &.header {
      .col-auto {
        display: flex;
        align-items: stretch;
      }
    }
  }
  .titulo-evento {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    flex-direction: column;
    height: 100%;
    // border-radius: 8px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    background-color: #444;
    color: #eee;
    font-size: 1.1em;
    font-weight: bold;
    line-height: 1;
    padding: 5px 10px;
  }
  .evento-datahora {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    padding: 5px 10px;
    // border-radius: 8px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    background-color: #444;
    color: #eee;
    font-size: 0.8em;
    font-weight: bold;
    line-height: 1;
    .evento-data {
      font-size: 1.2em;
    }
    .evento-hora {
      font-size: 1.1em;
    }
  }

  .disabled {
    // pointer-events: none;
  }
  .overlay-paused {
    position: absolute;
    top: 5.4em;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    .text-paused {
      color: #fff;
      font-size: 4em;
      font-weight: bold;
      text-shadow: 0 0 50px rgba(120, 6, 6, 0.7);
      text-align: center;
    }
  }
}
@media screen and (max-width: 991.98px) {
  .painelset-admin {
    .row {
      div[class^=col] {
        position: relative;
      }
    }
    .titulo-evento {
      font-size: 1em;
      padding: 5px 5px;
    }
    .cronometro-global {
      display: flex;
      height: 3.4em;
      .croncard {
        padding: 0;
      }
    }
    .overlay-paused {
      .text-paused {
        font-size: 3em;
      }
    }
  }
}
</style>
