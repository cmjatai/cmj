<template>
  <div
    :id="`vp-${item.__label__}-${item.id}`"
    :class="['voto-parlamentar']"
  >
    <div class="inner-voto">
      <button type="button" class="btn btn-lg btn-success" @click="sendVoto('Sim')">SIM</button>
      <button type="button" class="btn btn-lg btn-danger" @click="sendVoto('Não')">NÃO</button>
      <button type="button" class="btn btn-lg btn-warning" @click="sendVoto('Abstenção')">Abstenção</button>
    </div>
    <div class="voto-result" v-if="voto">
      <div class="avatar">
        <img
          :src="`/api/parlamentares/parlamentar/${authStore.data_connect.user.votante.parlamentar_id}/fotografia.c256.png`"
          :alt="authStore.data_connect.user.votante.nome_parlamentar"
          :title="authStore.data_connect.user.votante.nome_parlamentar"
        />
      </div>
      <div class="voto-computado">
        Voto Computado: <strong>{{ voto.voto }}</strong>
      </div>
    </div>
    <div class="voto-result" v-else>
      Voto não Computado
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import Resource from '~@/utils/resources'
import { computed, onMounted } from 'vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()
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

const voto = computed(() => {
  const field = props.item.__label__ === 'sessao_ordemdia' ? 'ordem' : 'expediente'
  const votos = Object.values(syncStore.data_cache?.sessao_votoparlamentar || {}).filter(
    v => v.parlamentar === authStore.data_connect.user.votante.parlamentar_id && v[field] === props.item.id
  )
  return votos.length > 0 ? votos[0] : null
})

function sendVoto(tipoVoto) {
  const field = props.item.__label__ === 'sessao_ordemdia' ? 'ordem' : 'expediente'
  const payload = {
    parlamentar: authStore.data_connect.user.votante.parlamentar_id,
    [field]: props.item.id,
    voto: tipoVoto
  }
  if (voto.value) {
    payload.id = voto.value.id

    Resource.Utils.patchModel({
      app: 'sessao',
      model: 'votoparlamentar',
      id: voto.value.id,
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

onMounted(() => {
  setTimeout(() => {
    const preview = document.getElementById(`is-${props.item.__label__}-${props.item.id}`)
    let curtop = 0
    let obj = preview
    do {
      curtop += obj.offsetTop
      obj = obj.offsetParent
    } while (obj && obj.tagName !== 'BODY')
    window.scrollTo({
      top: curtop - 100,
      behavior: 'smooth'
    })
  }, 100)
})

</script>
<style lang="scss">
.voto-parlamentar {
  position: absolute;
  top: 0em;
  right: 0em;
  left: 0;
  bottom: 0;
  display: flex;
  background-color: #000d;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  zoom: 2;
  z-index: 1;
  .inner-voto {
    display: flex;
    gap: 2em;
  }
  .voto-result {
    margin-top: 1em;
    color: #fff;
    font-size: 1.2em;
    background-color: #000A;
    padding: 0.5em 1em;
    border-radius: 0.5em;
    display: flex;
    align-items: center;
    gap: 1em;
    .avatar {
      width: 3em;
      height: 3em;
      border-radius: 50%;
      overflow: hidden;
      img {
        width: 100%;
        height: auto;
      }
    }
  }
  .btn {
    padding: 1em;
    line-height: 0;
    box-shadow: 0.5em 0.5em 1em #000;
    font-family: 'Graduate', 'Courier New', Courier, monospace;
    font-weight: bold;
    &:hover {
      box-shadow: 0.5em 0.5em 1em #222;
    }
  }
}

@media screen and (max-width: 991.98px) {
  .voto-parlamentar {
    zoom: 1.7;
  }
}
@media screen and (max-width: 800px) {
  .voto-parlamentar {
    zoom: 1.5;
  }
}
@media screen and (max-width: 600px) {
  .voto-parlamentar {
    zoom: 1;
  }
}
@media screen and (max-width: 480px) {
  .voto-parlamentar {
    zoom: 1;
    .inner-voto {
      gap: 1em;
    }
    .btn {
      padding: 1em 0.7em;
    }
  }
}
</style>
