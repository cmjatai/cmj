<template>
  <div class="portalcmj-connect">
    <div v-if="user" :class="['portalcmj-connected', is_expanded ? 'expand' : '']" @click.self="clickToggle">
      <div class="header">
        <div class="avatar" @click="clickToggle">
          <img v-if="user.votante" :src="`/api/parlamentares/parlamentar/${user.votante.parlamentar_id}/fotografia.c512.png`" :title="user.votante.nome_parlamentar"/>
          <img v-else :src="user.avatar" :title="user.fullname"/>
        </div>
        <div class="inner" v-if="is_expanded">
          <span v-if="user.votante" v-html="user.votante.nome_parlamentar"></span>
          <span v-if="!user.votante" v-html="user.fullname"></span><br>
          <small v-html="user.username"></small>
        </div>
      </div>
      <div class="rodape" v-if="is_expanded" @click="close" title="Desconectar usuário">
        Desconectar
        <FontAwesomeIcon icon="sign-out-alt" />
      </div>
    </div>
    <div v-if="!user" :class="['portalcmj-login', is_expanded ? 'expand' : '']" @click.self="clickToggle">
      <a class="header" @click="clickToggle">
        <FontAwesomeIcon icon="sign-in-alt" class="hover-circle animation-rotate" v-if="!is_expanded" :title="'Autenticar-se PortalCMJ'"/>
      </a>
      <div class="inner" v-if="is_expanded">
        <FontAwesomeIcon icon="times" class="fa-times hover-circle" @click="clickToggle" v-if="is_expanded" :title="'Fechar Janela de Autenticação'"/>
        <form class="inner-content" v-on:submit.prevent="submit">
          <h4>Entre com seu usuário e senha:</h4>
          <div class="alert alert-danger" v-if="error_message">Usuário e/ou Senha inválidos.</div>
          <div class="input-icon input_username">
            <FontAwesomeIcon icon="user" class="fa-user fa-2x "/>
            <input type="text" name="username" class="form-control" placeholder="Digite seu Endereço de email" autocomplete="username" maxlength="254" required="" id="id_username">
          </div>
          <div class="input-icon input_password">
            <FontAwesomeIcon icon="key" class="fa-key fa-2x "/>
            <input type="password" name="password" class="form-control" placeholder="Digite sua Senha" autocomplete="current-password" maxlength="30" required="" id="id_password">
          </div>
          <div class="rodape-login">
            <button class="btn btn-primary btn-login" type="submit" value="login">Conectar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '~@/stores/AuthStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'

const authStore = useAuthStore()
const messageStore = useMessageStore()

const is_expanded = ref(false)
const error_message = ref(false)

const user = computed(() => authStore.data_connect?.user || null)

const submit = (event) => {
  error_message.value = false
  authStore
    .loginPortalCMJ(
      event.target.elements.username.value,
      event.target.elements.password.value
    )
    .then((response) => {
      error_message.value = false
      messageStore.addMessage({
        type: 'info',
        text: 'Autenticação efetuada com sucesso!',
        timeout: 5000
      })
      clickToggle()
    })
    .catch((response) => {
      error_message.value = true
      // messageStore.sendMessage({ alert: 'danger', message: error.response.data.non_field_errors[0], time: 10 })
    })
}

const close = () => {
  authStore.logoutPortalCMJ()
    .then(() => {
      messageStore.addMessage({
        type: 'info',
        text: 'Desconectado com sucesso!',
        timeout: 5000
      })
    })
  is_expanded.value = false
}

const clickToggle = () => {
  authStore.loginStatus()
  is_expanded.value = !is_expanded.value
}

</script>

<style lang="scss">
.portalcmj-connect {
  position: relative;
  height: var(--height-header);
  .portalcmj-connected {
    cursor: pointer;
    // border-left: 1px solid var(--bs-border-color-translucent);
    width: var(--height-header);
    .avatar {
      width: 100%;
      height: auto;
      padding: 0.3em;
      opacity: 0.8;
      &:hover {
        opacity: 1;
      }
    }
  }
  .portalcmj-login, .portalcmj-connected {
    cursor: pointer;
    // border-left: 1px solid var(--bs-border-color-translucent);
    width: var(--height-header);
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;

    &.expand {
      position: fixed;
      width: 21em;
      height: auto;
      left: auto;
      top: 0;
      right: 0;
      bottom: 0;
      background-color: var(--bs-body-bg);
      box-shadow: -10px 0 20px var(--box-shadow-color);
      .inner {
        position: relative;
        display: flex;
        padding: 1em;
        width: 100%;
        .inner-content {
          width: 100%;
          padding: 1em;
        }
        .input-icon {
          position: relative;
          margin: 1.2em 0;
          width: 100%;
        }
        svg {
          position: absolute;
          top: 0.4em;
          left: 10px;
          opacity: 0.5;
        }
        svg.fa-times {
          position: absolute;
          top: 1.8em;
          right: 1em;
          left: auto;
        }
        .form-control {
          padding: 1em 1em 1em 3.3em;
          width: 100%;
          height: auto;
        }
        .rodape-login {
          text-align: right;
        }
      }
    }
  }

  .portalcmj-connected.expand {
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    .header {
      display: flex;
      align-items: center;
      flex-direction: column;
      width: 100%;
      padding-top: 2em;
      .inner {
        display: flex;
        align-items: center;
        flex-direction: column;
        line-height: 2;
      }
    }

    .avatar {
      width: 55%;
    }

    .rodape {
      text-align: right;
      width: 100%;
      padding: 1em;
      border-top: 1px solid var(--bs-border-color-translucent);
      cursor: pointer;
    }
  }
}

@media screen and (min-width: 600px) {
}

</style>
