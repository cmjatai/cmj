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
      </div>
      <div class="col-auto">
        <div class="btn-group">
          <a href="#" @click.prevent="resetToDefaults($event)" v-if="has_perm && !evento.end_real" class="btn btn-warning" title="Resetar Paineis para Padrão"><i class="fas fa-undo-alt"></i></a>
          <a href="#" @click.prevent="finish($event)" v-if="has_perm && evento.start_real && !evento.end_real" class="btn btn-danger" title="Encerrar Evento"><i class="fas fa-stop-circle"></i></a>
          <a href="#" @click.prevent="edit($event)" v-if="has_perm && !evento.end_real" class="btn btn-secondary" title="Editar Evento"><i class="fas fa-edit"></i></a>
          <a href="#" @click.prevent="copy($event)" v-if="has_perm && evento.end_real" class="btn btn-success" title="Duplicar Evento"><i class="fas fa-copy"></i></a>
          <a href="#" @click.prevent="admin($event)" v-if="has_perm && !evento.end_real" class="btn btn-primary" title="Execução do Evento"><i class="fas fa-toolbox"></i></a>
        </div>
      </div>
      <div class="col-12 mt-2">
        <div class="paineis pt-2">
          <strong>Painéis:</strong>
          <i class="fas fa-info-circle" title="Clique no nome do painel para abrir em uma nova aba."></i>
          <button class="btn btn-link" title="Adicionar novo painel ao evento" @click="createPainel($event)">
            <i class="fas fa-plus-circle"></i>
          </button>
          <ul>
            <li v-for="painel in paineis" :key="`painel-${painel.id}`" class="py-2">
              <div class="d-flex w-100 align-items-center">
                <a :href="`/painelset/painel/${painel.id}`" target="_blank">
                  {{ painel.name }}
                  <small v-if="painel.principal"><i class="fas fa-star"></i></small>
                </a><br>
                <button class="btn btn-link mr-2 text-danger" title="Adicionar novo painel ao evento" @click="deletePainel(painel.id)">
                  <i class="fas fa-minus-circle"></i>
                </button>
              </div>
              <span  class="sessao_list">
                <span>
                  &nbsp;&nbsp;- Sessão Vinculada:
                </span>
                <a
                  v-if="sessao_cache[painel.id]" :href="`${sessao_cache[painel.id]?.link_detail_backend}`" target="_blank">
                  <i class="fas fa-external-link-alt"></i>
                </a>
                <select
                  id="painel-sessao"
                  name="sessao_plenaria"
                  v-if="!evento.end_real"
                  v-model="painel.sessao"
                  @change="utils.patchModel('painelset', 'painel', painel.id, {sessao: painel.sessao })"
                >
                  <option :value="null">-- Nenhuma --</option>
                  <option
                    v-for="sessao in sessaoList"
                    :key="`sessao-option-${sessao.id}`"
                    :value="sessao.id"
                  >
                    {{ sessao.__str__ }} ({{ sessao.data_inicio }} - {{ sessao.data_fim || '' }})
                  </option>
                </select>
              </span>
            </li>
          </ul>
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
      has_perm: false
    }
  },
  computed: {
    sessaoList: function () {
      return _.orderBy(this.data_cache?.sessao_sessaoplenaria || [], ['data_inicio'], ['desc'])
    }
  },
  mounted: function () {
    const t = this
    t.has_perm = t.hasPermission('painelset.change_evento')
    t.refresh()
  },
  methods: {
    refresh () {
      const t = this
      t.utils.fetch({
        app: 'painelset',
        model: 'painel',
        query_string: `evento=${t.evento.id}`
      })
        .then((rp) => {
          t.paineis = rp.data.results
          rp.data.results.forEach(painel => {
            if (painel.sessao == null) {
              return
            }
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
            action: 'copy',
            method: 'PATCH'
          })
          .then(() => {
            this.sendMessage({ alert: 'success', message: 'Evento copiado com sucesso.', time: 5 })
          })
          .catch(() => {
            this.sendMessage({ alert: 'danger', message: 'Erro ao copiar evento. Verifique se o evento já foi finalizado.', time: 10 })
          })
      }
    },
    createPainel () {
      if (this.evento) {
        this.utils
          .postModel(
            'painelset',
            'painel', {
              name: `Painel do evento ${this.evento.name}`,
              description: `Painel criado automaticamente para o evento ${this.evento.name}`,
              evento: this.evento.id
            }
          )
          .then(() => {
            this.refresh()
            this.sendMessage({ alert: 'success', message: 'Painel criado com sucesso.', time: 5 })
          })
          .catch(() => {
            this.sendMessage({ alert: 'danger', message: 'Erro ao criar painel. Verifique se o evento já foi finalizado.', time: 10 })
          })
      }
    },
    deletePainel (painel_id) {
      if (painel_id) {
        this.utils
          .deleteModel(
            'painelset',
            'painel',
            painel_id
          )
          .then(() => {
            this.refresh()
            this.sendMessage({ alert: 'success', message: 'Painel deletado com sucesso.', time: 5 })
          })
          .catch(() => {
            this.sendMessage({ alert: 'danger', message: 'Erro ao deletar painel. Verifique se o evento já foi finalizado.', time: 10 })
          })
      }
    },
    finish () {
      if (this.evento) {
        this.fetchSync({
          app: 'painelset',
          model: 'evento',
          id: this.evento.id,
          action: 'finish',
          method: 'PATCH'
        })
      }
    },
    resetToDefaults () {
      if (this.evento) {
        this.utils.patchModelAction(
          'painelset',
          'evento',
          this.evento.id,
          'reset_to_defaults'
        )
          .then(() => {
            this.refresh()
            this.sendMessage({ alert: 'success', message: 'Paineis resetados para configuração padrão com sucesso.', time: 5 })
          })
          .catch(() => {
            this.sendMessage({ alert: 'danger', message: 'Erro ao resetar paineis para configuração padrão.', time: 10 })
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
  ul {
    background-color: #f5f5f5;
  }
  .container {
    margin-top: 20px;
  }
  .sessao_list {
    display: flex;
    gap: 0.7em;
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
