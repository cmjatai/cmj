<template>
  <div class="painelset-evento-list">
    <div class="header">
      <h1>Eventos</h1>
    </div>
    <div class="container">
      <div class="row" v-for="evento in eventos" :key="`evento-${evento.id}`">
        <div class="col">
          <h3 class="text-blue">{{ evento.name }}</h3>
          <strong>
            <span v-if="evento.start_real">Iniciado em: {{ start_real(evento) }}</span>
            <span v-else>Data e Hora Prevista: {{ start_previsto(evento) }}</span>
            <span>&nbsp;&nbsp;|&nbsp;&nbsp;Duração Estimada: {{ evento.duration }}</span>
            <span v-if="evento.end_real"><br>Finalizado em: {{ end_real(evento) }}</span>
          </strong><br>
          <span v-if="evento.description">
              {{ evento.description }}
          </span>
        </div>
        <div class="col-auto">
          <div class="btn-group">
            <a href="#" @click.prevent="finish(evento)" v-if="evento.start_real && !evento.end_real" class="btn btn-danger" title="Encerrar Evento"><i class="fas fa-stop-circle"></i></a>
            <a href="#" @click.prevent="edit(evento)" v-if="!evento.end_real" class="btn btn-secondary" title="Editar Evento"><i class="fas fa-edit"></i></a>
            <a href="#" @click.prevent="copy(evento)" v-if="evento.end_real" class="btn btn-success" title="Duplicar Evento"><i class="fas fa-copy"></i></a>
            <a href="#" @click.prevent="admin(evento)" v-if="!evento.end_real" class="btn btn-primary" title="Execução do Evento"><i class="fas fa-toolbox"></i></a>
          </div>
        </div>
      </div>
    </div>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'painelset-evento-list',
  data () {
    return {
    }
  },
  computed: {
    eventos: {
      get () {
        if (this.data_cache?.painelset_evento) {
          return _.orderBy(Object.values(this.data_cache.painelset_evento), ['start_real', 'start_previsto'], ['desc', 'desc'])
        }
        return []
      }
    }
  },
  mounted: function () {
    const t = this
    t.utils
      .hasPermission('painelset.change_evento')
      .then(hasPermission => {
        // t.fetchModelOrderedList('painelset', 'evento', '-start_real,-start_previsto')
        if (hasPermission) {
          t.fetchSync({
            app: 'painelset',
            model: 'evento',
            params: { o: '-start_real,-start_previsto' }
          })
        }
      })
  },
  methods: {
    admin (evento) {
      if (evento) {
        this.$router.push({ name: 'painelset_admin_link', params: { id: evento.id } })
      }
    },
    edit (evento) {
      if (evento) {
        window.open(evento.link_detail_backend, '_blank')
      }
    },
    copy (evento) {
      if (evento) {
        this
          .fetchSync({
            app: 'painelset',
            model: 'evento',
            id: evento.id,
            action: 'copy'
          })
          .then(() => {
            this.sendMessage({ alert: 'success', message: 'Evento copiado com sucesso.', time: 5 })
          })
          .catch(() => {
            this.sendMessage({ alert: 'danger', message: 'Erro ao copiar evento. Verifique se o evento já foi finalizado.', time: 10 })
          })
      }
    },
    finish (evento) {
      if (evento) {
        this.fetchSync({
          app: 'painelset',
          model: 'evento',
          id: evento.id,
          action: 'finish'
        })
      }
    },
    start_real (evento) {
      // formata evento.start_real para exibir na lista
      // de: 2025-10-12T13:39:50.386115-03:00 para: 2025-10-12 13:39
      return evento.start_real ? evento.start_real.replace('T', ' ').substring(0, 19) : ''
    },
    start_previsto (evento) {
      return evento.start_previsto ? evento.start_previsto.replace('T', ' ').substring(0, 19) : ''
    },
    end_real (evento) {
      return evento.end_real ? evento.end_real.replace('T', ' ').substring(0, 19) : ''
    }
  }
}
</script>

<style lang="scss">
.painelset-evento-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: auto;
  user-select: none;

  .header {
    background: white;
    padding: 10px 20px;
    h1 {
      margin: 0;
      font-weight: 600;
    }
  }

  .container {
    margin-top: 20px;
  }

  .row {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
  }

  .col-auto {
    display: flex;
    align-items: center;
    justify-content: center;
    .btn {
      font-size: 1em;
    }

  }
}
</style>
