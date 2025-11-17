<template>
  <div
    :id="`is-admin-${item.__label__}-${item.id}`"
    v-if="userIsAdminSessao"
    :class="['item-de-sessao-admin', actionsRunning ? 'actions-running' : '' ]"
  >
    <div class="inner-is-admin">
      <div
        class="btn-group"
        role="group"
        aria-label="Edição"
      >
        <a
          :href="item.link_detail_backend"
          target="_blank"
          :class="['btn', `btn-outline-secondary`]"
        >
          <FontAwesomeIcon icon="edit" />
        </a>
      </div>
      <div
        class="registro-leitura"
        v-if="item.tipo_votacao === 4"
      >
        <div
          class="btn-group"
          role="group"
          aria-label="State Leitura da matéria em Plenário"
        >
          <button
            type="button"
            :class="['btn', `btn-outline-${!item.votacao_aberta ? 'danger' : 'success' }`]"
            @click="toggleAction('votacao_aberta')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            data-bs-title="Abrir/Fechar para Leitura da matéria em Plenário"
          >
            <FontAwesomeIcon :icon="`${!item.votacao_aberta ? 'book' : 'book-open-reader'}`" />
          </button>
        </div>
        <div
          class="btn-group"
          role="group"
          aria-label="Registro de Leitura"
        >
          <button
            v-if="item.resultado"
            type="button"
            class="btn btn-outline-warning"
            @click="actionCancelarLeitura()"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Cancelar Registro de Leitura.`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="ban" />
          </button>
          <button
            v-if="item.votacao_aberta"
            type="button"
            class="btn btn-outline-primary"
            @click="actionRegistrarLeitura()"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Registrar Leitura da Matéria em Plenário.`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="book-open" />
          </button>
        </div>
      </div>
      <div
        v-else
        class="registro-votacao"
      >
        <div
          class="btn-group"
          role="group"
          :style="{ opacity: actionsRunning ? 0 : 1 }"
          aria-label="Registros de Votação Simbólica"
        >
          <button
            type="button"
            class="btn btn-outline-warning"
            @click="actionCancelarVotacao()"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Cancelar Registro de Votação.`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="ban" />
          </button>
          <button
            type="button"
            class="btn btn-outline-danger"
            @click="actionRegistrarVotacaoUnanime('R')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Registrar Rejeição Unânime sem voto do Presidente.`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="thumbs-down" />
          </button>
          <button
            type="button"
            class="btn btn-outline-primary"
            @click="actionRegistrarVotacaoUnanime('A')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Registrar Aprovação Unânime sem voto do Presidente.`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="thumbs-up" />
          </button>
        </div>
        <div
          class="btn-group"
          role="group"
          :style="{ opacity: actionsRunning ? 0 : 1 }"
          aria-label="Botões de controle de abertura de discussão, votação e pedido de adiamento"
        >
          <button
            type="button"
            :class="['btn', `btn-outline-${!item.discussao_aberta ? 'danger' : 'success' }`]"
            @click="toggleAction('discussao_aberta')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            data-bs-title="Abrir/Fechar para Discussão em Plenário"
          >
            <FontAwesomeIcon icon="comments" />&nbsp;
          </button>
          <button
            type="button"
            :class="['btn', `btn-outline-${!item.votacao_aberta ? 'danger' : 'success' }`]"
            @click="toggleAction('votacao_aberta')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            data-bs-title="Abrir/Fechar para Votação em Plenário"
          >
            <FontAwesomeIcon :icon="item.votacao_aberta ? 'book-open-reader' : 'book'" />&nbsp;
          </button>
          <button
            type="button"
            :class="['btn', `btn-outline-${!item.votacao_aberta_pedido_prazo ? 'danger' : 'success' }`]"
            @click="toggleAction('votacao_aberta_pedido_prazo')"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            data-bs-title="Abrir/Fechar para Votação de Pedido de Adiamento de Votação"
          >
            <i class="bi bi-hourglass-top" />
          </button>
        </div>

        <div
          v-if="item.votacao_aberta || item.votacao_aberta_pedido_prazo"
          class="btn-group"
          role="group"
          :style="{ opacity: actionsRunning ? 0 : 1 }"
          aria-label="Registro de Votação Simbólica sem unanimidade"
        >
          <button
            type="button"
            class="btn btn-outline-success"
            @click="votoParlamentarAdminOpened = true"
            data-bs-toggle="tooltip"
            data-bs-placement="top"
            :data-bs-title="`Registrar Votação`"
            :disabled="actionsRunning"
          >
            <FontAwesomeIcon icon="check-to-slot" />
          </button>
        </div>
      </div>
    </div>
    <Loading
      v-if="actionsRunning"
      message="Registrando..."
      position="absolute"
    />
    <Teleport
      v-if="votoParlamentarAdminOpened"
      :to="`#modalCmj`"
    >
      <VotoParlamentarAdmin
        :key="`vpa-${item.__label__}-${item.id}`"
        :item="item"
        :sessao="sessao"
        @close="votoParlamentarAdminOpened = false"
        @register="actionRegistrar"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { useAuthStore } from '~@/stores/AuthStore'
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resource from '~@/utils/resources'
import Loading from '~@/components/atoms/Loading.vue'
import { computed, onMounted, ref, watch } from 'vue'
import { Tooltip } from 'bootstrap'
import VotoParlamentarAdmin from '../votacao/VotoParlamentarAdmin.vue'

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

const actionsRunning = ref(false)
const votoParlamentarAdminOpened = ref(false)

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

const actionRegistrarVotacaoUnanime = async (
  aprovacaoRejeicao
) => {
  actionRegistrar({
    action: 'action_registrovotacao',
    form: {
      unanime: true,
      resultado: aprovacaoRejeicao,
      com_presidente: false
    }
  })
}

const actionRegistrarLeitura = async () => {
  actionRegistrar({
    action: 'action_registroleitura',
    form: {}
  })
}

const actionRegistrar = async (metadata) => {
  actionsRunning.value = true
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    id: props.item.id,
    action: metadata.action,
    form: metadata.form
  }).then((result) => {
    console.log('Votação registrada com sucesso', result)
    actionsRunning.value = false
  }).catch((err) => {
    actionsRunning.value = false
    messageStore.addMessage({
      type: err.response.data.type || 'danger',
      text: err.response.data.detail || 'Erro ao registrar votação!',
      timeout: 5000
    })
  })
}

const actionCancelarLeitura = async () => {
  actionsRunning.value = true
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    action: 'action_cancelar_registroleitura',
    id: props.item.id
  }).then((result) => {
    actionsRunning.value = false
    console.log('Registro de leitura cancelado com sucesso', result)
  }).catch((err) => {
    actionsRunning.value = false
    messageStore.addMessage({
      type: 'warning',
      text: err.response.data.detail || 'Erro ao cancelar registro de leitura!',
      timeout: 5000
    })
  })
}

const actionCancelarVotacao = async () => {
  actionsRunning.value = true
  votoParlamentarAdminOpened.value = false
  const [app, model] = props.item.__label__.split('_')
  Resource.Utils.patchModel({
    app,
    model,
    action: 'action_cancelar_registrovotacao',
    id: props.item.id
  }).then((result) => {
    actionsRunning.value = false
    console.log('Registro de votação cancelado com sucesso', result)
  }).catch((err) => {
    actionsRunning.value = false
    messageStore.addMessage({
      type: 'warning',
      text: err.response.data.detail || 'Erro ao cancelar registro de votação!',
      timeout: 5000
    })
  })
}

onMounted(() => {
  refreshTooltips(2000)
})

watch(
  () => props.item,
  () => {
    refreshTooltips(500)
  }
)

const refreshTooltips = (timeout) => {
  setTimeout(() => {
    // capturar todos elementos da classe 'tooltip bs-tooltip-auto' e destruir-los
    const tooltipListOld = document.querySelectorAll('.tooltip.bs-tooltip-auto')
    tooltipListOld.forEach((tooltip) => {
      tooltip.remove()
    })
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [
      ...tooltipTriggerList
    ].map(tooltipTriggerEl => new Tooltip(
      tooltipTriggerEl,
      {
        trigger: 'hover'
      }
    ))
  }, timeout)
}

</script>

<style lang="scss">
.item-de-sessao-admin {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  &.actions-running {
    pointer-events: none;
    user-select: none;
    height: 100%;
  }
  .inner-is-admin {
    position:absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 0.3em;
    z-index: 10;
    margin-bottom: 0.3em;
    display: flex;
    gap: 0.5em;
  }

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
