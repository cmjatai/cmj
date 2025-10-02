<template>
  <div class="painelset-admin">
    <div class="container-fluid p-2">
      <div class="row header mx-n2">
        <div class="col-auto">
          <cronometro
            v-if="cronometro"
            :cronometro_id="cronometro.id"
            css_class_controls="hover"
            css_class="cronometro-global"
            ></cronometro>
        </div>
        <div class="col">
          <div class="titulo-evento">
            {{ evento ? evento.name : 'Carregando evento...' }}
          </div>
        </div>
        <div class="col-auto">
          <div class="evento-datahora">
            <div class="evento-data">
              {{ evento && evento.start_previsto ? (new Date(evento.start_previsto)).toLocaleDateString() : 'Data não definida' }}
            </div>
            <div class="evento-hora">
              {{ evento && evento.start_previsto ? (new Date(evento.start_previsto)).toLocaleTimeString() : 'Hora não definida' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vuex from 'vuex'
import Cronometro from '../components/Cronometro.vue'
export default {
  name: 'painelset-admin',
  components: {
    Cronometro
  },
  data () {
    return {
      evento: null,
      cronometro: null
    }
  },

  mounted: function () {
    this.fetchEvento()
  },
  methods: {
    ...Vuex.mapActions([
      'getObject'
    ]),
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
          if (t.evento && t.evento.cronometro) {
            t.cronometro = t.evento.cronometro
          } else {
            t.utils.getModelAction(
              'painelset',
              'evento',
              eventoId,
              'cronometro'
            ).then(cronometro => {
              t.cronometro = cronometro.data
              t.evento.cronometro = cronometro.data
            }).catch(err => {
              console.error('Erro ao buscar o cronometro do evento', err)
            })
          }
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
      .box {
        background-color: #444;
        color: #fff;
        border-radius: 8px;
        padding: 5px 10px 3px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        .inner {
          height: 100%;
        }
      }
    }
  }
}
</style>
