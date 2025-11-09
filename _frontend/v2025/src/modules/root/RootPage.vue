<template>
  <root-layout>
    <template #header-left>
      <button
        class="d-lg-none"
        type="button"
        data-bs-toggle="offcanvas"
        data-bs-target="#menuSideLeft"
        aria-controls="menuSideLeft"
      >
        ☰
      </button>
    </template>

    <template #brand>
      <brand />
    </template>

    <template #header-detail>
      <div
        class="btn-group btn-group-sm accessibility"
        role="group"
        aria-label="First group"
      >
        <a
          href="#"
          class="btn btn-secondary"
          @click.prevent="clickFullscreen"
          :title="fullscreen ? 'Sair do modo tela cheia' : 'Entrar no modo tela cheia'"
        >
          <FontAwesomeIcon :icon="fullscreen ? 'compress' : 'expand'" />
        </a>
      </div>
      <div
        class="btn-group btn-group-sm accessibility"
        role="group"
        aria-label="Second group"
      >
        <a
          class="btn btn-secondary"
          @click="diminuirFonte"
        >a</a>
        <a
          class="btn btn-secondary"
          @click="aumentarFonte"
        >A</a>
      </div>
    </template>

    <template #header-right>
      <portal-cmj-connect />
    </template>

    <template #sideleft>
      <side-left />
    </template>

    <template #sideright>
      <side-right />
    </template>

    <template #main>
      <router-view />
    </template>
  </root-layout>
</template>

<script setup>
import PortalCmjConnect from '~@/components/PortalCmjConnect.vue'
import RootLayout from './RootLayout.vue'
import SideLeft from './SideLeft.vue'
import SideRight from './SideRight.vue'
import Brand from './Brand.vue'
import { ref } from 'vue'
// 1. Imports

// 2. Composables

// 3. Props & Emits

// 4. State & Refs
const fullscreen = ref(false)
document.addEventListener('fullscreenchange', () => {
  fullscreen.value = !!document.fullscreenElement
})

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks
const clickFullscreen = () => {
  fullscreen.value = !fullscreen.value
  if (fullscreen.value) {
     if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen()
    } else if (document.documentElement.webkitRequestFullscreen) { /* Safari */
      document.documentElement.webkitRequestFullscreen()
    } else if (document.documentElement.msRequestFullscreen) { /* IE11 */
      document.documentElement.msRequestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) { /* Safari */
      document.webkitExitFullscreen()
    } else if (document.msExitFullscreen) { /* IE11 */
      document.msExitFullscreen()
    }
  }
}

const diminuirFonte = () => {
  $('.root-layout .main').css('font-size', '-=1')
}
const aumentarFonte = () => {
  $('.root-layout .main').css('font-size', '+=1')
}
// 8. Functions
</script>
<style lang="scss">
.root-layout {

}
</style>
