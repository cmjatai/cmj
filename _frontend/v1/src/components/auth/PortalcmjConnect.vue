<template>
  <div class="portalcmj-connect">
    <div v-if="user" :class="['portalcmj-connected', is_expanded ? 'expand' : '']" @click.self="clickToggle">
      <div class="header">
        <div class="avatar" @click="clickToggle">
          <img v-if="user.votante" :src="`/api/parlamentares/parlamentar/${user.votante.parlamentar_id}/fotografia.c256.png`" :title="user.votante.nome_parlamentar"/>
          <img v-else :src="user.avatar" :title="user.fullname"/>
        </div>
        <div class="inner" v-if="is_expanded">
          <span v-if="user.votante" v-html="user.votante.nome_parlamentar"></span>
          <span v-if="!user.votante" v-html="user.fullname"></span><br>
          <small v-html="user.username"></small>
        </div>
      </div>
      <div class="rodape" v-if="is_expanded" @click="close" >
        Desconectar
        <i :class="[`fas fa-sign-out-alt hover-circle`]" title="Desconectar usuário"></i>
      </div>
    </div>
    <div v-if="!user" :class="['portalcmj-login', is_expanded ? 'expand' : '']" @click.self="clickToggle">
      <div class="header"  @click="clickToggle">
        <i :class="[`fas fa-sign-in-alt hover-circle`]" v-if="!is_expanded" title="Autenticar-se PortalCMJ"></i>
      </div>
      <div class="inner" v-if="is_expanded">
        <i :class="[`fas fa-times`]" @click="clickToggle" v-if="is_expanded" title="Fechar Janela de Autenticação"></i>
        <form class="inner-content"  v-on:submit.prevent="submit">
          <h4>Entre com seu usuário e senha:</h4>
          <div class="alert alert-danger" v-if="error_message">Usuário e/ou Senha inválidos.</div>
          <div class="input-icon input_username">
            <span class="fa fa-user fa-2x "></span>
            <input type="text" name="username" class="form-control" placeholder="Digite seu Endereço de email" autocomplete="username" maxlength="254" required="" id="id_username">
          </div>
          <div class="input-icon input_password">
            <span class="fa fa-key fa-2x "></span>
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
<script>
import { EventBus } from '@/event-bus'
export default {
  name: 'portalcmj-connect',
  data () {
    return {
      is_expanded: false,
      error_message: false,
      app: [
        'core',
        'parlamentares'
      ],
      model: [
        'votante',
        'user'
      ]
    }
  },
  beforeDestroy: function () {
    this.$disconnect()
  },
  computed: {
  },
  methods: {
    fetch (metadata) {
      // chamado pelo push do servidor
      // if (metadata === undefined) {
      //   return
      // }
      // if (metadata.app === 'parlamentares' && metadata.model === 'votante') {
      //   if (metadata.id === t.item.materia || metadata.id in t.materia.anexadas) {
      //   }
    },
    clickToggle () {
      this.is_expanded = !this.is_expanded
    },
    close () {
      const t = this
      t.clickToggle()
      t
        .logoutPortalCMJ()
        .then((response) => {
          t.sendMessage({ alert: 'info', message: 'Desconexão efetuada com sucesso!', time: 5 })
          // window.location.href = '/'
          EventBus.$emit('user-logged-out')
        })
    },
    submit (evt) {
      const t = this
      t.error_message = false
      t
        .loginPortalCMJ({
          username: evt.target.elements.username.value,
          password: evt.target.elements.password.value
        })
        .then((response) => {
          t.error_message = false
          t.sendMessage({ alert: 'info', message: 'Autenticação efetuada com sucesso!', time: 5 })
          t.clickToggle()
          EventBus.$emit('user-logged-in')
        })
        .catch(() => {
          t.error_message = true
          // t.sendMessage({ alert: 'danger', message: error.response.data.non_field_errors[0], time: 10 })
        })
    }

  }
}
</script>
<style lang="scss">
.portalcmj-connect {
  position: relative;
  .avatar {
    cursor: pointer;
    width: 48px;
    height: 48px;
    text-align: center;
  }
  .portalcmj-connected, .portalcmj-login {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .expand {
    position: fixed;
    left: 70%;
    right: 0;
    bottom: 0;
    background-color: #eeee;
    border-left: 1px solid #fff;
    box-shadow: -10px 0 20px #fff;
    justify-content: space-between;
    .avatar {
      width: 60%;
      height: auto;
      padding: 1em;
      opacity: 1;
    }
    .header {
      text-align: center;
      width: 100%;
    }
    .rodape {
      text-align: right;
      width: 100%;
      padding: 0.5em;
      border-top: 1px solid #fff;
      cursor: pointer;
      &:hover {
        background-color: #ccc;
      }
    }
  }
  .portalcmj-login {
    &.expand{
      justify-content: center;
      .header {
        position: relative;
      }
      .rodape-login {
        text-align: right;
      }
      .inner {
        position: relative;
        display: flex;
        padding: 1em;
        width: 100%;
        .fa-times {
          position: absolute;
          top: 1.8em;
          right: 1em;
        }
        .inner-content {
          background-color: #fff;
          width: 100%;
          padding: 1em;
        }
        .input-icon {
          position: relative;
          margin: 1em 0;
          width: 100%;
        }
        span {
          position: absolute;
          top: 0.4em;
          left: 10px;
          opacity: 0.5;
        }
        .form-control {
          padding: 1em 1em 1em 3em;
          width: 100%;
          height: auto;
        }
      }
    }
  }
}

@media screen and (max-width: 991.98px) {
  .portalcmj-connect {
    .expand {
      left: 60%;
    }
  }
}

@media screen and (max-width: 767.98px) {
  .portalcmj-connect {
    .expand {
      left: 50%;
    }
  }
}

@media screen and (max-width: 575.98px) {
  .portalcmj-connect {
    .expand {
      left: 30%;
    }
  }
}

</style>
