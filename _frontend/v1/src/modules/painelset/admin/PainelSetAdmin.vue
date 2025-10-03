<template>
  <div class="painelset-admin">
    <div class="container-fluid p-2">
      <div class="row header mx-n2">
        <div class="col-auto">
          <cronometro-global
            v-if="cronometro"
            :cronometro_id="cronometro.id"
            css_class_controls="hover"
            css_class="cronometro-global"
            :controls="['start', 'pause', 'resume', 'toggleDisplay']"
            @cronometro_start="fetchEvento()"
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
    </div>
  </div>
</template>

<script>
import Vuex from 'vuex'
import CronometroGlobal from '../components/CronometroGlobal.vue'
export default {
  name: 'painelset-admin',
  components: {
    CronometroGlobal
  },
  data () {
    return {
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
    this.fetchEvento()
  },
  methods: {
    ...Vuex.mapActions([
      'getObject'
    ]),
    refreshEvento () {
      const t = this
      t
        .refreshState({
          app: 'painelset',
          model: 'evento',
          id: t.evento.id
        })
        .then((evento) => {
          t.evento = evento
        })
    },
    fetchEvento () {
      const t = this
      const eventoId = this.$route.params.id
      if (!eventoId) {
        return
      }
      t
        .getObject({
          app: 'painelset',
          model: 'evento',
          id: eventoId
        })
        .then(evento => {
          t.evento = evento
          t.utils.getModelAction(
            'painelset',
            'evento',
            eventoId,
            'cronometro'
          ).then(cronometro => {
            t.cronometro = cronometro.data
            t.evento.cronometro = cronometro.data
            t.refreshEvento()
          }).catch(err => {
            console.error('Erro ao buscar o cronometro do evento', err)
          })
        })
        .catch(err => {
          console.error('Erro ao buscar o evento', err)
        })
    }
  }
}
</script>

<style lang="scss">
.painelset-admin {
  $px: 10px;
  line-height: 1;
  .row {
    align-items: stretch;
    .col, .col-auto {
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
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
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
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
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
