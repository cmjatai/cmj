<template>
  <div :class="['row', 'painelset-evento-list-item', { 'evento-finalizado': evento && evento.end_real }]">
    <div class="col">
      <h3 class="text-blue">
        {{ evento.name }}
      </h3>
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
        <a
          href="#"
          @click.prevent="finish($event)"
          v-if="has_perm && !evento.end_real"
          class="btn btn-danger"
          title="Encerrar Evento"
        ><FontAwesomeIcon icon="stop-circle" /></a>
        <a
          href="#"
          @click.prevent="edit($event)"
          v-if="has_perm && !evento.end_real"
          class="btn btn-secondary"
          title="Editar Evento"
        ><FontAwesomeIcon icon="edit" /></a>
        <a
          href="#"
          @click.prevent="copy($event)"
          v-if="has_perm && evento.end_real"
          class="btn btn-success"
          title="Duplicar Evento"
        ><FontAwesomeIcon icon="copy" /></a>
        <a
          href="#"
          @click.prevent="admin($event)"
          v-if="has_perm && !evento.end_real"
          class="btn btn-primary"
          title="Execução do Evento"
        ><FontAwesomeIcon icon="toolbox" /></a>
      </div>
    </div>
    <div class="col-12 mt-2">
      <div class="paineis pt-2">
        <strong>Painéis:</strong>
        <FontAwesomeIcon
          icon="info-circle"
          title="Clique no nome do painel para abrir em uma nova aba."
        />
        <div
          class="btn-group btn-group-sm d-inline-flex pl-1 mb-n2"
          v-if="has_perm && !evento.end_real"
        >
          <a
            :href="`/api/painelset/evento/${evento.id}/export.yaml?t=${Date.now()}`"
            class="btn btn-info"
            title="Exportar Paineis do Evento em YAML"
          >
            <FontAwesomeIcon icon="file-download" />
          </a>
          <button
            @click.prevent="resetToDefaults($event)"
            class="btn btn-warning"
            title="Resetar Paineis para Padrão"
          >
            <FontAwesomeIcon icon="undo-alt" />
          </button>
          <button
            class="btn btn-primary"
            title="Adicionar novo painel ao evento"
            @click="createPainel($event)"
          >
            <FontAwesomeIcon icon="plus-circle" />
          </button>
        </div>
        <ul>
          <li
            v-for="painel in paineis"
            :key="`painel-${painel.id}`"
            class="py-2"
          >
            <div class="d-flex w-100 align-items-center">
              <a
                :href="`/painelset/painel/${painel.id}`"
                target="_blank"
              >
                {{ painel.name }}
                <small
                  v-if="painel.principal"
                  title="Painel Principal"
                ><FontAwesomeIcon icon="star" /></small>
              </a><br>
              <button
                v-if="has_perm"
                class="btn btn-link mr-2 text-danger"
                title="Remover Painel do Evento"
                @click="deletePainel(painel.id)"
              >
                <FontAwesomeIcon icon="minus-circle" />
              </button>
            </div>
            <div class="sessao_list">
              <span class="text-nowrap">
                &nbsp;&nbsp;- Sessão Vinculada:
              </span>
              <a
                v-if="sessao_cache[painel.id]"
                :href="`${sessao_cache[painel.id]?.link_detail_backend}`"
                target="_blank"
              >
                <FontAwesomeIcon icon="external-link-alt" />
                <span v-if="!has_perm"> {{ sessao_cache[painel.id]?.__str__ }}</span>
              </a>
              <div
                class="d-inline-block"
                v-if="has_perm"
              >
                <select
                  class="form-control form-control-sm"
                  :id="`painel-sessao-${painel.id}`"
                  :name="`sessao_plenaria-${painel.id}`"
                  v-if="!evento.end_real"
                  v-model="painel.sessao"
                  @change="
                    Resources.Utils.patchModel({
                      app: 'painelset', model: 'painel', id: painel.id, form: {sessao: painel.sessao }
                    }).then(() => {
                      refresh()
                    })
                  "
                >
                  <option :value="null">
                    -- Nenhuma --
                  </option>
                  <option
                    v-for="sessao in sessaoList"
                    :key="`sessao-option-${sessao.id}`"
                    :value="sessao.id"
                  >
                    {{ sessao.__str__ }} ({{ sessao.data_inicio }} - {{ sessao.data_fim || '' }})
                  </option>
                </select>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resources from '~@/utils/resources'

const router = useRouter()
const syncStore = useSyncStore()
const authStore = useAuthStore()
const messageStore = useMessageStore()

const props = defineProps({
  evento: {
    type: Object,
    required: true
  }
})

const sessao_cache = reactive({})
const paineis = ref({})
const reload = ref(false)

const sessaoList = computed(() => {
  return _.orderBy(syncStore.data_cache?.sessao_sessaoplenaria || [], ['data_inicio'], ['desc'])
})

const has_perm = computed(() => {
  return authStore.permissions.includes('painelset.change_evento')
})

const refresh = () => {
  Resources.Utils.fetch({
    app: 'painelset',
    model: 'painel',
    query_string: `evento=${props.evento.id}`
  })
    .then((rp) => {
      paineis.value = rp.data.results
      rp.data.results.forEach(painel => {
        if (painel.sessao == null) {
          return
        }
        Resources.Utils.fetch({
          app: 'sessao',
          model: 'sessaoplenaria',
          id: painel.sessao
        })
          .then(r => {
            sessao_cache[painel.id] = r.data
          })
      })
    })
    .catch(() => {
      console.debug('Erro ao buscar paineis do evento.')
      if (reload.value === false) {
        reload.value = true
        setTimeout(() => {
          refresh()
        }, 5000)
      }
    })
}

const admin = () => {
  if (props.evento) {
    router.push({ name: 'painelsetadmin_admin_link', params: { id: props.evento.id } })
  }
}

const edit = () => {
  if (props.evento) {
    window.open(props.evento.link_detail_backend, '_blank')
  }
}

const copy = () => {
  if (props.evento) {
    Resources.Utils.patchModel({
      app: 'painelset',
      model: 'evento',
      id: props.evento.id,
      action: 'copy'
    })
      .then(() => {
        messageStore.addMessage({ type: 'success', text: 'Evento copiado com sucesso.', timeout: 5000 })
      })
      .catch(() => {
        messageStore.addMessage({ type: 'danger', text: 'Erro ao copiar evento. Verifique se o evento já foi finalizado.', timeout: 10000 })
      })
  }
}

const createPainel = () => {
  if (props.evento) {
    Resources.Utils
      .postModel({
        app: 'painelset',
        model: 'painel',
        form: {
          name: `Painel do evento ${props.evento.name}`,
          description: `Painel criado automaticamente para o evento ${props.evento.name}`,
          evento: props.evento.id
        }
      })
      .then(() => {
        refresh()
        messageStore.addMessage({ type: 'success', text: 'Painel criado com sucesso.', timeout: 5000 })
      })
      .catch(() => {
        messageStore.addMessage({ type: 'danger', text: 'Erro ao criar painel. Verifique se o evento já foi finalizado.', timeout: 10000 })
      })
  }
}

const deletePainel = (painel_id) => {
  if (painel_id) {
    Resources.Utils
      .deleteModel({
        app: 'painelset',
        model: 'painel',
        id: painel_id
      })
      .then(() => {
        refresh()
        messageStore.addMessage({ type: 'success', text: 'Painel deletado com sucesso.', timeout: 5000 })
      })
      .catch(() => {
        messageStore.addMessage({ type: 'danger', text: 'Erro ao deletar painel. Verifique se o evento já foi finalizado.', timeout: 10000 })
      })
  }
}

const finish = () => {
  if (props.evento) {
    Resources.Utils.patchModel({
      app: 'painelset',
      model: 'evento',
      id: props.evento.id,
      action: 'finish'
    })
  }
}

const resetToDefaults = () => {
  if (props.evento) {
    Resources.Utils.patchModel({
      app: 'painelset',
      model: 'evento',
      id: props.evento.id,
      action: 'reset_to_defaults'
    })
      .then(() => {
        refresh()
        messageStore.addMessage({ type: 'success', text: 'Paineis resetados para configuração padrão com sucesso.', timeout: 5000 })
      })
      .catch(() => {
        messageStore.addMessage({ type: 'danger', text: 'Erro ao resetar paineis para configuração padrão.', timeout: 10000 })
      })
  }
}

const start_real = () => {
  return props.evento.start_real ? props.evento.start_real.replace('T', ' ').substring(0, 19) : ''
}

const start_previsto = () => {
  return props.evento.start_previsto ? props.evento.start_previsto.replace('T', ' ').substring(0, 19) : ''
}

const end_real = () => {
  return props.evento.end_real ? props.evento.end_real.replace('T', ' ').substring(0, 19) : ''
}

onMounted(() => {
  refresh()
})
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
    align-items: center;
    padding-right: 0.5em;
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
