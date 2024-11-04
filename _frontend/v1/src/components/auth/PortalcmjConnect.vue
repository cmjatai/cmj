<template>
  <div class="portalcmj-connect">
    <div v-if="user" :class="['portalcmj-connected', is_expanded ? 'expand' : '']">
      <div class="header">
        <div class="avatar" @click="clickToggle">
          <img v-if="user.votante" :src="`/api/parlamentares/parlamentar/${user.votante.parlamentar_id}/fotografia.c256.png`" :title="user.votante.nome_parlamentar"/>
          <img v-else :src="user.avatar" :title="user.fullname"/>
        </div>
        <div class="inner" v-if="is_expanded">
          <span v-html="user.votante.nome_parlamentar"></span><br>
          <small v-html="user.username"></small>
        </div>
      </div>
      <div class="rodape" v-if="is_expanded" @click="close" >
        Desconectar
        <i :class="[`fas fa-sign-out-alt hover-circle`]" title="Desconectar usuário"></i>
      </div>
    </div>
    <div v-if="!user" :class="['portalcmj-login', is_expanded ? 'expand' : '']">
      <div class="header" v-if="!is_expanded" @click="clickToggle">
        <i :class="[`fas fa-sign-in-alt hover-circle`]" title="Autenticar-se PortalCMJ"></i>
      </div>
      <div class="inner" v-if="is_expanded">
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
          <button class="btn btn-primary btn-login" type="submit" value="login">Conectar</button>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'portalcmj-connect',
  data () {
    return {
      is_expanded: false,
      error_message: false
    }
  },
  beforeDestroy: function () {
    this.$disconnect()
  },
  computed: {
  },
  methods: {
    clickToggle () {
      this.is_expanded = !this.is_expanded
    },
    close () {
      this.clickToggle()
      this
        .logoutPortalCMJ()
        .then((response) => {
          this.sendMessage({ alert: 'info', message: 'Desconexão efetuada com sucesso!', time: 5 })
          // window.location.href = '/'
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
      .inner {
        display: flex;
        background-color: #fff;
        padding: 2em;
        width: 90%;
        .inner-content {
          width: 100%;
          text-align: center;
        }
        .input-icon {
          position: relative;
          margin: 1em 0;
          width: 100%;
        }
        span {
          position: absolute;
          top: 0.3em;
          left: 10px;
          opacity: 0.6;
        }
        .form-control {
          padding: 1em 3em;
          width: 100%;
          height: auto;
        }
      }
    }
  }
}
</style>
