<template>
  <base-layout>

    <template slot="brand">
      <brand></brand>
    </template>
    <template slot="header-detail">
      <nivel-detalhe v-if="nivel_detalhe_visivel"></nivel-detalhe>
      <div class="btn-group btn-group-sm accessibility" role="group" aria-label="First group">
        <a href="#" class="btn btn-outline-dark" @click.prevent="fullscreen = !fullscreen" :title="fullscreen ? 'Sair do modo tela cheia' : 'Entrar no modo tela cheia'">
          <i :class="fullscreen ? 'fas fa-compress' : 'fas fa-expand'"></i>
        </a>
      </div>
      <div class="btn-group btn-group-sm accessibility" role="group" aria-label="Second group">
        <a class="btn btn-outline-dark" @click="diminuirFonte">a</a>
        <a class="btn btn-outline-dark" @click="aumentarFonte">A</a>
      </div>
    </template>

    <template slot="header-right">
      <portalcmj-connect></portalcmj-connect>
    </template>

    <template slot="sideleft" :sideleft_visivel="sideleft_visivel">
      <side-left></side-left>
      <div :class="['ws-status', ws_status]" :title="ws_status === 'connected' ? 'Conexão ativa' : 'Sem conexão com o servidor. Tentando reconectar...'">
        <div class="inner">
          <i :class="ws_status === 'connected' ? 'fas fa-wifi' : 'fas fa-exclamation-triangle'"></i>
        </div>
      </div>
    </template>

    <template slot="sideright" :sideright_visivel="sideright_visivel">
      <side-right></side-right>
    </template>

    <template slot="main">
      <router-view></router-view>
    </template>

  </base-layout>
</template>

<script>

import workerTimer from '@/timer/worker-timer'

import PortalcmjConnect from '@/components/auth/PortalcmjConnect'
import SideRight from './fragments/SideRight'
import SideLeft from './fragments/SideLeft'
import Brand from './fragments/Brand'
import BaseLayout from './fragments/BaseLayout'
import NivelDetalhe from './sessao/NivelDetalhe'
import Vuex from 'vuex'

export default {
  name: 'online',
  components: {
    PortalcmjConnect,
    BaseLayout,
    SideRight,
    SideLeft,
    Brand,
    NivelDetalhe
  },
  data () {
    return {
      fullscreen: false,
      count_time: 0,
      id_interval: 0,
      ws_status: 'disconnected' // connected, disconnected
    }
  },
  watch: {
    fullscreen (newVal) {
      if (newVal) {
        document.getElementsByClassName('online-module')[0].parentElement.requestFullscreen()
      } else {
        if (document.fullscreenElement) {
          document.exitFullscreen()
        }
      }
    }
  },
  computed: {
    ...Vuex.mapGetters([
      'nivel_detalhe_visivel',
      'sideleft_visivel',
      'sideright_visivel'
    ])
  },
  // implementar redirect de vue-router se a url for /online para /online/sessao
  beforeRouteEnter (to, from, next) {
    if (to.path === '/online' || to.path === '/online/') {
      next('/online/sessao')
    } else {
      next()
    }
  },
  beforeDestroy: function () {
    try {
      this.$options.sockets.onmessage = null
      this.$disconnect()
      console.log('WebSocket timerefresh disconnected')
    } catch (e) {
      console.log(e) // Logs the error
    }
  },
  mounted: function () {
    try {
      const t = this
      t.$options.sockets.onmessage = t.handleWebSocketMessageTimeRefresh
      t.$options.sockets.onopen = function () {
        t.ws_status = 'connected'
      }
      t.$options.sockets.onclose = function () {
        t.ws_status = 'disconnected'
      }
      document.addEventListener('fullscreenchange', (event) => {
        if (!document.fullscreenElement) {
          t.fullscreen = false
        }
      })
    } catch (e) {
      console.log(e) // Logs the error
    }
  },
  methods: {
    diminuirFonte () {
      $('.base-layout .main').css('font-size', '-=1')
    },
    aumentarFonte () {
      $('.base-layout .main').css('font-size', '+=1')
    },
    ws_monitor_connection () {
      // console.log('scroll')
      let t = this
      if (t.count_time === 0) {
        t.count_time += 1
        if (t.id_interval !== 0) {
          workerTimer.clearInterval(t.id_interval)
        }
        t.id_interval = workerTimer.setInterval(() => {
          // console.log(t.count_time, new Date())
          if (t.ws_status === 'disconnected') {
            // console.log('reconnect')
            t.count_time = 11
            t.ws_monitor_connection()
            return
          }
          t.count_time += 1
          if (t.count_time > 60) { // 5 minutos
            t.ws_monitor_connection()
          }
        }, 6000)
      } else if (t.count_time > 10) {
        workerTimer.clearInterval(t.id_interval)
        t.id_interval = 0
        // console.log('reconnect')
        t.count_time = 0
        t.ws_reconnect()
        t.ws_monitor_connection()
      } else {
        t.count_time = 0
      }
    }
  }
}
</script>

<style lang="scss">
.ws-status {
  color: white;
  //text-align: center;
  font-size: 0.75rem;
  z-index: 10;
  .inner {
    display: inline-block;
    padding: 3px;
  }
  &.connected {
    .inner {
      background-color: rgba(green, 0.7);
    }
  }
  &.disconnected {
    .inner {
      background-color: rgba(red, 0.7);
    }
  }
}
.header-right {
  display: grid;
  align-items: stretch;
  justify-items: stretch;
  z-index: 2;
  i {
    color: rgba(black, 0.5);
    padding: 8px;
    cursor: pointer;
    &:hover {
      color: black;
    }
  }
}
</style>
