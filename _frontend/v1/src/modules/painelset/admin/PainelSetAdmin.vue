<template>
  <div class="painelset-admin">
    <div class="container-fluid">
      <div class="row">
        <div class="col-6">
          a<cronometro v-if="cronometro" :cronometro_id="cronometro.id"></cronometro>
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
</style>
