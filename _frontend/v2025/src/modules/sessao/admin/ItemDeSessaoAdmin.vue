<template>
  <div
    :id="`is-admin-${item.__label__}-${item.id}`"
    v-if="userIsAdminSessao"
    class="item-de-sessao-admin"
  >
    <div
      class="registro-leitura"
      v-if="item.tipo_votacao === 4"
    >
      <div
        class="btn-group"
        role="group"
        aria-label="Administração do item de sessão"
      >
        <button
          type="button"
          :class="['btn', `btn-${!item.votacao_aberta ? 'danger' : 'success' }`]"
          @click="toggleAction('votacao_aberta')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          data-bs-title="Abrir/Fechar para Leitura da matéria em Plenário"
        >
          <FontAwesomeIcon :icon="`${!item.votacao_aberta ? 'book' : 'book-open-reader'}`" />
        </button>
      </div>
    </div>
    <div
      v-else
      class="registro-votacao"
    >
      <div
        v-if="!actionsDisabled"
        class="btn-group"
        role="group"
        aria-label="Botões de controle de abertura de discussão, votação e pedido de adiamento"
      >
        <button
          type="button"
          :class="['btn', `btn-${!item.discussao_aberta ? 'danger' : 'success' }`]"
          @click="toggleAction('discussao_aberta')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          data-bs-title="Abrir/Fechar para Discussão em Plenário"
        >
          <FontAwesomeIcon icon="comments" />&nbsp;
        </button>
        <button
          type="button"
          :class="['btn', `btn-${!item.votacao_aberta ? 'danger' : 'success' }`]"
          @click="toggleAction('votacao_aberta')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          data-bs-title="Abrir/Fechar para Votação em Plenário"
        >
          <FontAwesomeIcon :icon="item.votacao_aberta ? 'book-open-reader' : 'book'" />&nbsp;
        </button>
        <button
          type="button"
          :class="['btn', `btn-${!item.votacao_aberta_pedido_prazo ? 'danger' : 'success' }`]"
          @click="toggleAction('votacao_aberta_pedido_prazo')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          data-bs-title="Abrir/Fechar para Votação de Pedido de Adiamento de Votação"
        >
          <i class="bi bi-hourglass-top" />
        </button>
      </div>
      <div
        v-if="!actionsDisabled && item.tipo_votacao === 1"
        class="btn-group"
        role="group"
        aria-label="Registros de Votação Simbólica"
      >
        <button
          type="button"
          class="btn btn-warning"
          @click="actionCancelarVotacao()"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :data-bs-title="`Cancelar Registro de Votação.`"
          :disabled="actionsDisabled"
        >
          <FontAwesomeIcon icon="ban" />
        </button>
        <button
          type="button"
          class="btn btn-danger"
          @click="actionRegistrarVotacao('R')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :data-bs-title="`Registrar Rejeição Unânime sem voto do Presidente.`"
          :disabled="actionsDisabled"
        >
          <FontAwesomeIcon icon="thumbs-down" />
        </button>
        <button
          type="button"
          class="btn btn-primary"
          @click="actionRegistrarVotacao('A')"
          data-bs-toggle="tooltip"
          data-bs-placement="top"
          :data-bs-title="`Registrar Aprovação Unânime sem voto do Presidente.`"
          :disabled="actionsDisabled"
        >
          <FontAwesomeIcon icon="thumbs-up" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '~@/stores/AuthStore'
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resource from '~@/utils/resources'
import { computed, onMounted, ref } from 'vue'
import { Tooltip } from 'bootstrap'

const authStore = useAuthStore()
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

const actionsDisabled = ref(false)

const userIsAdminSessao = computed(() => {
  return authStore.hasPermission('sessao.add_sessaoplenaria')
})

const toggleAction = async (action) => {
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    form: {
      field: action
    },
    action: 'toggle_state',
    id: props.item.id
  }).then((result) => {
    console.log('Discussão alterada com sucesso', result)
  }).catch((err) => {
    console.error('Erro ao alterar discussão', err)
  })
}

const actionRegistrarVotacao = async (aprovacaoRejeicao) => {
  actionsDisabled.value = true
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    form: {
      unanime: aprovacaoRejeicao,
      com_presidente: false
    },
    action: 'action_registrovotacao_unanime',
    id: props.item.id
  }).then((result) => {
    console.log('Votação registrada com sucesso', result)
    actionsDisabled.value = false
  }).catch((err) => {
    actionsDisabled.value = false
    messageStore.addMessage({
      type: err.response.data.type || 'danger',
      text: err.response.data.detail || 'Erro ao registrar votação!',
      timeout: 5000
    })
  })
}

const actionCancelarVotacao = async () => {
  actionsDisabled.value = true
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    action: 'action_cancelar_registrovotacao',
    id: props.item.id
  }).then((result) => {
    actionsDisabled.value = false
    console.log('Registro de votação cancelado com sucesso', result)
  }).catch((err) => {
    actionsDisabled.value = false
    messageStore.addMessage({
      type: 'warning',
      text: err.response.data.detail || 'Erro ao cancelar registro de votação!',
      timeout: 5000
    })
  })
}

onMounted(() => {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [
    ...tooltipTriggerList
  ].map(tooltipTriggerEl => new Tooltip(
    tooltipTriggerEl,
    {
      trigger: 'hover'
    }
  ))
})

</script>

<style lang="scss">
.item-de-sessao-admin {
  position: absolute;
  left: 50%;
  bottom: 0em;
  // border: 1px solid var(--bs-border-color);
  border-radius: 0.3em;
  margin-bottom: 0.3em;
  transform: translateX(-50%);
  z-index: 10;

  .registro-votacao, .registro-leitura {
    display: flex;
    gap: 0.5em;
    .btn-group {
      background-color: var(--bs-body-bg);
      &:hover {
        box-shadow: 1px 1px 0.5em 0.5em var(--bs-body-bg);
      }
    }
  }

}
</style>
