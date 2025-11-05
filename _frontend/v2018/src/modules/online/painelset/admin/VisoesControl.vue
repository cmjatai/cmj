<template>
  <div class="painelset-visoes-control">
    <div class="youtube_id">
      <input type="text" v-model="evento.youtube_id" @change="
        utils.patchModel(
          'painelset',
          'evento',
          evento.id,
          { youtube_id: evento.youtube_id }
        )"/>
    </div>
    <div class="inner-visoes">
      <div class="checkbox-auto-select-visoes">
        <input
          type="checkbox"
          id="autoSelectVisoes"
          v-model="painel.auto_select_visoes"
          @change="
            utils.patchModel(
              'painelset',
              'painel',
              painel.id,
              { auto_select_visoes: painel.auto_select_visoes }
            )
          "
        >
      </div>
      <div class="lista-visoes btn-group">
        <a
          v-for="visao in visoes" :key="`visao-control-${visao.id}`"
          :class="['btn btn-secondary', visao.active ? 'active' : '']"
          :title="visao.name"
          @click="manualActiveVisao(visao.id)"
        >
          {{ visao.position }}
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'visoes-control',
  props: {
    evento: {
      type: Object,
      required: true
    }
  },
  components: {
  },
  data () {
    return {
      evento_id: Number(this.$route.params.id)
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
        if (newVal) {
          this.fetchSync({
            app: 'painelset',
            model: 'painel',
            params: {
              evento: newVal.id,
              principal: true
            }
          })
            .then(() => {
              this.fetchSync({
                app: 'painelset',
                model: 'visaodepainel',
                params: { painel: this.painel.id }
              })
            })
        }
      },
      immediate: true
    }
  },
  computed: {
    painel: function () {
      if (this.evento && this.data_cache?.painelset_painel) {
        return Object.values(this.data_cache?.painelset_painel).find(p => p.evento === this.evento.id) || null
      }
      return null
    },
    visoes: function () {
      if (this.painel && this.data_cache?.painelset_visaodepainel) {
        return _.orderBy(
          _.filter(
            Object.values(this.data_cache?.painelset_visaodepainel),
            { painel: this.painel.id }
          ),
          ['position'],
          ['asc']
        )
      }
      return []
    }
  },
  mounted: function () {
    this.$nextTick(() => {
      if (this.hasPermission('painelset.change_evento')) {
        this.registerModels({
          app: 'painelset',
          models: ['evento', 'painel', 'visaodepainel']
        })
        this.fetchSync({
          app: 'painelset',
          model: 'evento',
          id: this.evento_id
        })
      } else {
        this.$router.push({ name: 'online_index_link' })
        this.sendMessage({ alert: 'danger', message: 'Você não tem permissão para acessar esta página.', time: 5 })
      }
    })
  },
  methods: {
    manualActiveVisao: function (visao_id) {
      this
        .utils.patchModelAction(
          'painelset', 'visaodepainel', visao_id, 'activate'
        )
        .then(response => {

        })
        .catch(error => {
          console.error(this.evento.id, 'active', error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar Visão Ativa: ' + error.response.data, time: 5 })
        })
    }
  }
}
</script>

<style lang="scss">
.painelset-visoes-control {
  position: absolute;
  left: 37%;
  right: 0;
  bottom: 0em;
  background-color: #222;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  .inner-visoes {
    display: flex;
    flex-direction: row;
    align-items: center;
  }

  .checkbox-auto-select-visoes {
    zoom: 2;
    input {
      margin: 0 0.5em;
    }
  }
  .youtube_id {
    width: 100%;
    padding: 0.5em 0.5em 0;
    input {
      width: 100%;
    }
  }

  .lista-visoes {
    display: flex;
    flex-direction: row;
    margin: 0.5em;
    .btn {
      padding-left: 2em;
      padding-right: 2em;
    }
  }
}
@media (max-width: 768px) {
  .painelset-visoes-control {
    left: 0;
    right: 0;
    bottom: 0em;
    .checkbox-auto-select-visoes {
      zoom: 1.5;
      input {
        margin: 0 0.3em;
      }
    }
    .lista-visoes {
      .btn {
        padding-left: 0.6em;
        padding-right: 0.6em;
      }
    }
  }
}
</style>
