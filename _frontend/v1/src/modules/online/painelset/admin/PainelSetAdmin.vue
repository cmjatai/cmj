<template>
  <div class="painelset-admin">
    <div class="container-fluid">
      <div class="row header">
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
        <div class="col">
          <div class="titulo-evento">
            {{ evento ? evento.name : 'Carregando evento...' }}
          </div>
        </div>
        <div class="col-auto">
          <div class="evento-datahora">
            {{ datahora_prevista_real[0] }}
            <div class="evento-data">
               {{ datahora_prevista_real[1] }}
            </div>
            <div class="evento-hora">
              {{ datahora_prevista_real[2] }}
            </div>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-7 container-individuos">
          <individuo-list v-if="evento" :evento="evento" :ref="'individuoList'"></individuo-list>
        </div>
        <div class="col-5 container-controls">
          controles aqui
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CronometroGlobal from '../components/cronometros/CronometroGlobal.vue'
import IndividuoList from './IndividuoList.vue'
export default {
  name: 'painelset-admin',
  components: {
    CronometroGlobal,
    IndividuoList
  },
  data () {
    return {
      app: [
        'painelset'
      ],
      model: [
        'evento'
      ],
      evento: null,
      cronometro: null
    }
  },
  computed: {
    datahora_prevista_real: function () {
      if (this.evento && !this.evento.start_real) {
        const dt = new Date(this.evento.start_previsto)
        return ['Início previsto', dt.toLocaleDateString(), dt.toLocaleTimeString()]
      } else if (this.evento && this.evento.start_real) {
        const dt = new Date(this.evento.start_real)
        return ['Início real', dt.toLocaleDateString(), dt.toLocaleTimeString()]
      }
      return ['Data e hora não definidas', '', '']
    }
  },
  mounted: function () {
    this.$nextTick(() => {
      this.fetch(
        {
          app: 'painelset',
          model: 'evento',
          id: Number(this.$route.params.id)
        }
      )
    })
  },
  methods: {
    fetch (metadata) {
      const t = this
      if (t.evento) {
        console.log('WebSocket message received:', metadata)
      }
      if (!t.evento || metadata.id === t.evento.id) {
        t
          .refreshState(metadata)
          .then((obj) => {
            t.evento = obj
            t
              .refreshState({
                app: 'painelset',
                model: 'cronometro',
                id: obj.cronometro
              })
              .then((cronometro) => { t.cronometro = cronometro })
          })
          .catch((err) => {
            console.error('Erro ao atualizar o evento', err)
          })
      }
    },
    resumeEvento () {
      this.$refs.individuoList.status_microfone = 1
    },
    startEvento () {
      this.$refs.individuoList.status_microfone = 1
      this.utils.getModelAction('painelset', 'evento', this.evento.id, 'start')
        .then(response => {
          this.cronometro = response.data
        })
        .catch(error => {
          console.error('start error', error)
        })
    },
    pauseEvento () {
      this.$refs.individuoList.status_microfone = 0
    }
  }
}
</script>

<style lang="scss">
.painelset-admin {
  $px: 10px;
  line-height: 1;
  .container-fluid {
    padding: 0 $px;
  }
  .row {
    align-items: stretch;
    margin-left: -$px;
    margin-right: -$px;
    padding-top: $px;
    div[class^=col] {
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
    align-items: center;
    justify-content: center;
    height: 100%;
    // border-radius: 8px;
    // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    background-color: #fff;
    color: #333;
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
    background-color: #fff;
    color: #333;
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
  .cronometro-component {
    &.cronometro-global {
      font-size: 1.6em;
      font-weight: bold;
      .card {
        .inner {
        }
      }
    }
  }
}
</style>
