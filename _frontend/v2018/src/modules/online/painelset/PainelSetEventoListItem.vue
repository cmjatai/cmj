<template>
  <div :class="['row', 'painelset-evento-list-item', { 'evento-finalizado': evento && evento.end_real }]" >
      <div class="col">
        <h3 class="text-blue">{{ evento.name }}</h3>
        <strong>
          <span v-if="evento.start_real">Iniciado em: {{ start_real() }}</span>
          <span v-else>Data e Hora Prevista: {{ start_previsto() }}</span>
          <span>&nbsp;&nbsp;|&nbsp;&nbsp;Duração Estimada: {{ evento.duration }}</span>
          <span v-if="evento.end_real"><br>Finalizado em: {{ end_real() }}</span>
        </strong><br>
        <span v-if="evento.description">
            {{ evento.description }}
        </span>
        <div class="paineis pt-2">
          <strong>Painéis:</strong>
          <ul>
            <li v-for="painel in paineis" :key="`painel-${painel.id}`">
              <a :href="`/painelset/painel/${painel.id}`" target="_blank">{{ painel.name }}</a><br>
              &nbsp;&nbsp;- Sessão: {{ sessao_cache[painel.id]?.__str__ }}
            </li>
          </ul>
        </div>
      </div>
      <div class="col-auto">
        <div class="btn-group">
          <a href="#" @click.prevent="finish($event)" v-if="hasPermission && evento.start_real && !evento.end_real" class="btn btn-danger" title="Encerrar Evento"><i class="fas fa-stop-circle"></i></a>
          <a href="#" @click.prevent="edit($event)" v-if="hasPermission && !evento.end_real" class="btn btn-secondary" title="Editar Evento"><i class="fas fa-edit"></i></a>
          <a href="#" @click.prevent="copy($event)" v-if="hasPermission && evento.end_real" class="btn btn-success" title="Duplicar Evento"><i class="fas fa-copy"></i></a>
          <a href="#" @click.prevent="admin($event)" v-if="hasPermission && !evento.end_real" class="btn btn-primary" title="Execução do Evento"><i class="fas fa-toolbox"></i></a>
        </div>
      </div>
    </div>
</template>

<script>

export default {
  name: 'painelset-evento-list-item',
  props: {
    evento: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
      sessao_cache: {},
      paineis: {},
      hasPermission: false
    }
  },
  computed: {
  },
  mounted: function () {
    const t = this

    t.utils
      .hasPermission('painelset.change_evento')
      .then(hasPermission => {
        if (hasPermission) {
          t.hasPermission = true
        }
      })

    t.utils.fetch({
      app: 'painelset',
      model: 'painel',
      query_string: `evento=${t.evento.id}`
    })
      .then((rp) => {
        t.paineis = rp.data.results
        rp.data.results.forEach(painel => {
          this.utils.fetch({
            app: 'sessao',
            model: 'sessaoplenaria',
            id: painel.sessao
          })
            .then(r => {
              t.$set(t.sessao_cache, painel.id, r.data)
            })
        })
      })
  },
  methods: {
    admin () {
      if (this.evento) {
        this.$router.push({ name: 'painelset_admin_link', params: { id: this.evento.id } })
      }
    },
    edit () {
      if (this.evento) {
        window.open(this.evento.link_detail_backend, '_blank')
      }
    },
    copy () {
      if (this.evento) {
        this
          .fetchSync({
            app: 'painelset',
            model: 'evento',
            id: this.evento.id,
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
    finish () {
      if (this.evento) {
        this.fetchSync({
          app: 'painelset',
          model: 'evento',
          id: this.evento.id,
          action: 'finish'
        })
      }
    },
    start_real () {
      // formata evento.start_real para exibir na lista
      // de: 2025-10-12T13:39:50.386115-03:00 para: 2025-10-12 13:39
      return this.evento.start_real ? this.evento.start_real.replace('T', ' ').substring(0, 19) : ''
    },
    start_previsto () {
      return this.evento.start_previsto ? this.evento.start_previsto.replace('T', ' ').substring(0, 19) : ''
    },
    end_real () {
      return this.evento.end_real ? this.evento.end_real.replace('T', ' ').substring(0, 19) : ''
    }
  }
}
</script>

<style lang="scss">
.painelset-evento-list-item {
  &.evento-finalizado {
    background-color: #e0e0e0;
    color: #777;
    h3, a:not(.btn) {
      color: #999 !important;
    }
  }
  &:hover {
    background-color: #f0f0f0;
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
