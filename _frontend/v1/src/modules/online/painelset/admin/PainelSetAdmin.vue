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
          <cronometro-global
            v-if="cronometro"
            :cronometro_id="cronometro.id"
            css_class_controls="hover"
            css_class="cronometro-global"
            :controls="['start', 'pause', 'resume', 'toggleDisplay']"
            @cronometro_start="startEvento()"
            @cronometro_pause="pauseEvento()"
            @cronometro_resume="resumeEvento()"
            ></cronometro-global>
        </div>
      </div>
      <div class="row">
        <div class="col-4 container-individuos">
          <individuo-list v-if="evento" :evento="evento" :ref="'individuoList'" @onload="onIndividuoListLoad()" :pause_parent_on_start="cronometro && cronometro.pause_parent_on_start"></individuo-list>
        </div>
        <div class="col-8 container-controls">
          <palavra-em-uso v-if="individuoListLoaded"></palavra-em-uso>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CronometroGlobal from '../components/cronometros/CronometroGlobal.vue'
import IndividuoList from './IndividuoList.vue'
import PalavraEmUso from './PalavraEmUso.vue'
export default {
  name: 'painelset-admin',
  components: {
    CronometroGlobal,
    IndividuoList,
    PalavraEmUso
  },
  data () {
    return {
      evento_id: Number(this.$route.params.id),
      individuoListLoaded: false
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
    onIndividuoListLoad: function () {
      this.individuoListLoaded = true
    },
    resumeEvento () {
      this.$refs.individuoList.status_microfone = 0
      this.$refs.individuoList.toggleAllMicrofones()
    },
    startEvento () {
      this.utils.getModelAction('painelset', 'evento', this.evento.id, 'start')
        .then(response => {
          console.log('start response', response)
          this.cronometro = response.data
        })
        .catch(error => {
          console.error('start error', error)
        })
    },
    pauseEvento () {
      this.$refs.individuoList.status_microfone = 1
      this.$refs.individuoList.toggleAllMicrofones()
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
  }
  .cronometro-global {
    display: flex;
    height: 3.4em;
    .croncard {
      padding: 0;
    }
  }
}
</style>
