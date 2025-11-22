<template>
  <div
    :id="`vpa-${item.__label__}-${item.id}`"
    class="modal voto-parlamentar-admin-modal-view fade show"
    tabindex="-1"
  >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5
            class="modal-title"
          >
            Registro de Votação dos Parlamentares
            <small class="d-inline-block ps-3 ">
              {{ materia ? materia.__str__ : '' }}
            </small>
          </h5>
          <button
            type="button"
            class="btn-close"
            @click="emit('close')"
          />
        </div>
        <div
          class="modal-body"
        >
          <div class="row">
            <div class="col-md-6">
              <div class="votos-parlamentares-list">
                <div
                  class="voto-parlamentar-header voto-parlamentar-item font-weight-bold"
                >
                  <div class="nome-parlamentar">
                    <h5>Votos dos Parlamentares</h5>
                  </div>
                  <div class="voto-parlamentar-options">
                    <button
                      type="button"
                      :class="['btn btn-sm', 'btn-outline-success']"
                      @click="sendVoto(0, 'Sim')"
                    >
                      SIM
                    </button>
                    <button
                      type="button"
                      :class="['btn btn-sm', 'btn-outline-danger']"
                      @click="sendVoto(0, 'Não')"
                    >
                      NÃO
                    </button>
                    <button
                      type="button"
                      :class="['btn btn-sm', 'btn-outline-warning']"
                      @click="sendVoto(0, 'Abstenção')"
                    >
                      Abstenção
                    </button>
                  </div>
                </div>
                <div
                  :id="`voto-parlamentar-${parlamentar.id}`"
                  class="voto-parlamentar-item"
                  v-for="parlamentar in parlamentaresPresentes"
                  :key="`voto-parlamentar-${parlamentar.id}`"
                >
                  <div class="nome-parlamentar">
                    {{ parlamentar.nome_parlamentar }}
                  </div>
                  <div
                    class="voto-parlamentar-options"
                    v-if="votosParlamentares"
                  >
                    <button
                      type="button"
                      :class="['btn btn-sm', `btn${votosParlamentares[parlamentar.id]?.voto === 'Sim' ? '-success' : '-outline-success'}`]"
                      @click="sendVoto(parlamentar.id, 'Sim')"
                    >
                      SIM
                    </button>
                    <button
                      type="button"
                      :class="['btn btn-sm', `btn${votosParlamentares[parlamentar.id]?.voto === 'Não' ? '-danger' : '-outline-danger'}`]"
                      @click="sendVoto(parlamentar.id, 'Não')"
                    >
                      NÃO
                    </button>
                    <button
                      type="button"
                      :class="['btn btn-sm', `btn${votosParlamentares[parlamentar.id]?.voto === 'Abstenção' ? '-warning' : '-outline-warning'}`]"
                      @click="sendVoto(parlamentar.id, 'Abstenção')"
                    >
                      Abstenção
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <div>
                  <strong class="p-2 d-inline-block">
                    Tipo de Resultado da Votação:
                    *
                  </strong>
                  <select
                    id="tipo-resultado-votacao"
                    class="form-select"
                    v-model="form.tipo_resultado_votacao"
                  >
                    <option
                      v-for="tipo in tiposResultadoVotacao"
                      :key="`tipo-resultado-votacao-${tipo.id}`"
                      :value="tipo.id"
                    >
                      {{ tipo.__str__ }}
                    </option>
                  </select>
                </div>
                <div>
                  <strong class="pt-4 pb-2 d-inline-block">
                    Observações:
                  </strong>
                  <textarea
                    class="form-control"
                    rows="5"
                    v-model="form.observacao"
                  />
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button
                type="button"
                class="btn btn-secondary"
                @click="actionCancelarVotacao()"
              >
                Cancelar Registro de Votação
              </button>
              <button
                type="button"
                class="btn btn-success"
                @click="actionRegistrarVotacao()"
              >
                Registrar e Fechar Votação
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resource from '~@/utils/resources'
import { computed, ref } from 'vue'

const emit = defineEmits(['close', 'register', 'cancel'])

const syncStore = useSyncStore()
const messageStore = useMessageStore()

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  sessao: {
    type: Object,
    required: true
  }
})

const materia = computed(() => {
  const materias = Object.values(
    syncStore.data_cache?.materia_materialegislativa || {}).filter(
    m => m.id === props.item.materia
  )
  return materias.length > 0 ? materias[0] : null
})

const parlamentaresPresentes = computed(() => {
  const model_presenca = props.item.__label__ === 'sesso_ordemdia' ? 'sessao_presencaordemdia' : 'sessao_sessaoplenariapresenca'
  const presentes = Object.values(
    syncStore.data_cache?.[model_presenca] || {}).filter(
    p => p.sessao_plenaria === props.sessao.id)
  return presentes.map(p => {
    const parlamentar = syncStore.data_cache?.parlamentares_parlamentar?.[p.parlamentar]
    return parlamentar ? parlamentar : null
  })
})

const votosParlamentares = computed(() => {
  const votos_cache = syncStore.data_cache?.sessao_votoparlamentar || {}
  const field = props.item.__label__ === 'sessao_ordemdia' ? 'ordem' : 'expediente'
  const votos_do_item = Object.values(votos_cache).filter(
    v => v[field] === props.item.id && v.votacao === null
  )
  return votos_do_item.reduce((acc, voto) => {
    acc[voto.parlamentar] = voto
    return acc
  }, {})
})

const form = ref({
  tipo_resultado_votacao: null,
  observacao: ''
})
const tiposResultadoVotacao = computed(() => {
  return Object.values(
    syncStore.data_cache?.sessao_tiporesultadovotacao || {}
  ).filter(
    trv => (trv.natureza === 'P' && props.item.votacao_aberta_pedido_prazo === true) ||
           (trv.id > 0 && props.item.votacao_aberta_pedido_prazo === false)
  )
})

const actionCancelarVotacao = () => {
  Object.values(votosParlamentares.value).forEach(voto => {
    console.debug('deletando voto', voto)
    Resource.Utils.deleteModel({
      app: 'sessao',
      model: 'votoparlamentar',
      id: voto.id
    })
  })
  emit('close')
}

const sendVoto = (parlamentarId, tipoVoto) => {

  if (!parlamentarId) {
    // voto em massa
    Object.values(parlamentaresPresentes.value).forEach(parlamentar => {
      sendVoto(parlamentar.id, tipoVoto)
    })
    return
  }

  const field = props.item.__label__ === 'sessao_ordemdia' ? 'ordem' : 'expediente'
  const payload = {
    votacao: null,
    parlamentar: parlamentarId,
    [field]: props.item.id,
    voto: tipoVoto
  }

  const voto = votosParlamentares.value[parlamentarId]

  if (voto && voto.voto === tipoVoto) {
    // delete o voto existente
    Resource.Utils.deleteModel({
      app: 'sessao',
      model: 'votoparlamentar',
      id: voto.id
    })
      .then(() => {
        messageStore.addMessage({
          type: 'info',
          text: 'Voto Removido!',
          timeout: 5000
        })
      })
      .catch(() => {
        // erro ao deletar voto
        messageStore.addMessage({
          type: 'danger',
          text: 'Erro ao remover voto. Tente novamente.',
          timeout: 5000
        })
      })
    return
  }

  if (voto) {
    payload.id = voto.id
    Resource.Utils.patchModel({
      app: 'sessao',
      model: 'votoparlamentar',
      id: voto.id,
      form: payload
    })
      .then(() => {
        messageStore.addMessage({
          type: 'info',
          text: 'Voto Atualizado!',
          timeout: 5000
        })
      })
      .catch(() => {
        // erro ao atualizar voto
        messageStore.addMessage({
          type: 'danger',
          text: 'Erro ao computar voto. Tente novamente.',
          timeout: 5000
        })
      })

  }
  else {
    Resource.Utils.postModel({
      app: 'sessao',
      model: 'votoparlamentar',
      form: payload
    })
      .then(() => {
        messageStore.addMessage({
          type: 'info',
          text: 'Voto Computado!',
          timeout: 5000
        })
      })
      .catch(() => {
        // erro ao criar voto
        messageStore.addMessage({
          type: 'danger',
          text: 'Erro ao computar voto. Tente novamente.',
          timeout: 5000
        })
      })
  }
}

const actionRegistrarVotacao = () => {
  emit('register', {
    action: 'action_registrovotacao',
    form: {
      ...form.value,
      unanime: false,
      com_presidente: false
    }
  })
  emit('close')
}

</script>

<style lang="scss">

.voto-parlamentar-admin-modal-view {
  background-color: #000b;
  z-index: 10000;
  display: block;

  .votos-parlamentares-list {
    border: 1px solid var(--bs-border-color);
    margin-bottom: 1em;
    border-radius: 0.5em;
    overflow: hidden;
  }
  .voto-parlamentar-header {
    background-color: var(--bs-body-color);
    color: var(--bs-body-bg);
  }

  .voto-parlamentar-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    &:not(:last-child) {
      border-bottom: 1px solid var(--bs-border-color);
    }

    .nome-parlamentar {
      font-weight: bold;
    }

    .voto-parlamentar-options {
      gap: 0.5em;
      display: flex;
      .btn-outline-success,
      .btn-outline-danger,
      .btn-outline-warning {
        opacity: 0.7;
      }
    }
  }
  .voto-parlamentar-header {
    .btn {
      opacity: 1 !important;
    }
  }
}

</style>
