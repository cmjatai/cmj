<template>
  <div
    ref="popoverPalavra"
    class="popover-palavra"
    v-if="individuos"
    @touchstart="touching = true"
    @touchmove="movePopover($event)"
    @touchend="touching = false"
    @mouseup="touching = false"
    @mousemove="movePopover($event)"
    @mousedown="touching = true"
    >
    <div :class="['popover-individuo', individuo.com_a_palavra ? 'com_a_palavra': 'aparteante']" v-for="individuo in individuos" :key="`popover-individuo-${individuo.id}`">
      <div class="popover-header">
        <div class="arrow"></div>
        <h3
          class="popover-title"
          v-if="individuo.com_a_palavra"
        >
          <font-awesome-icon icon="fa-solid fa-arrows-up-down-left-right" />
          <span>
            Com a palavra
          </span>
        </h3>
        <h3 class="popover-title" v-if="individuo.aparteado">Em aparte</h3>
      </div>
      <div class="popover-body">
        <div v-if="individuo" class="individuo-info">
          <div class="info">
            <div class="name">{{ individuo.name }}</div>
            <div class="timer mt-1" v-if="individuo.cronometro">
              <WidgetCronometroBase
                :cronometro-id="individuo.cronometro"
                :key="`cronometro-popover-${individuo.cronometro}`"
                :ref="`cronometro-popover-${individuo.cronometro}`"
                css_class_controls="d-none"
                class="cron-popover-palavra"
                :display-initial="'remaining'"
                :display-format="'mm:ss'"
                :display-size="'2em'"
                :display-permitidos="['remaining']"
                :controls="[]"
              ></WidgetCronometroBase>
            </div>
          </div>
          <div
            class="foto me-2"
            v-if="fotografiaUrl(individuo)"
            :style="{ backgroundImage: 'url(' + fotografiaUrl(individuo) + ')' }"
          />
          <div class="foto me-2" v-else>
            <FontAwesomeIcon :icon="['fas', 'user']" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import WidgetCronometroBase from '~@/modules/painelset/widgets/painelset/WidgetCronometroBase.vue'

import { useSyncStore } from '~@/stores/SyncStore'
import { computed, ref, onMounted } from 'vue'

const syncStore = useSyncStore()

const touching = ref(false)
const moving = ref(false)

const popoverPalavra = ref(null)

const individuoComPalavra = computed(() => {
  return syncStore.data_cache?.painelset_individuo
    ? Object.values(syncStore.data_cache.painelset_individuo).filter(ind => ind.com_a_palavra)
    : []
})

const individuoAparteante = computed(() => {
  return syncStore.data_cache?.painelset_individuo
    ? Object.values(syncStore.data_cache.painelset_individuo).filter(ind => ind.aparteado)
    : []
})

const individuos = computed(() => {
  return [...individuoComPalavra.value, ...individuoAparteante.value]
})

onMounted(() => {
  syncStore.registerModels('painelset', [
    'individuo', 'cronometro'
  ])
})

const fotografiaUrl = (individuo) => {
  if (individuo.parlamentar) {
    return '/api/parlamentares/parlamentar/' + individuo.parlamentar + '/fotografia.c96.png'
  } else if (individuo.fotografia) {
    return '/api/painelset/individuo/' + individuo.id + '/fotografia.c96.png'
  }
  return null
}

const movePopover = (event) => {
  if (!touching.value)
    return

    const popover = popoverPalavra.value
    const rect = popover.getBoundingClientRect()

    // se for touch, detectar dois toques e alterar fontSize de acordo com a distancia.
    if (event.touches && event.touches.length > 1) {
      event.preventDefault() // prevent scrolling
      const distance = Math.hypot(
        event.touches[0].clientX - event.touches[1].clientX,
        event.touches[0].clientY - event.touches[1].clientY
      )
      const newFontSize = Math.min(Math.max(distance / 10, 10), 100) // constrain between 10px and 60px
      popover.style.fontSize = `${newFontSize}px`
      return
    }

    // Get pointer position (mouse or touch)
    const clientX = event.touches ? event.touches[0].clientX : event.clientX
    const clientY = event.touches ? event.touches[0].clientY : event.clientY

    // Calculate new position (center popover on cursor)
    const newRight = window.innerWidth - clientX - rect.width / 2
    const newBottom = window.innerHeight - clientY - rect.height / 2

    // Constrain to viewport
    const constrainedRight = Math.max(0, Math.min(newRight, window.innerWidth - rect.width))
    const constrainedBottom = Math.max(0, Math.min(newBottom, window.innerHeight - rect.height))

    popover.style.right = `${constrainedRight}px`
    popover.style.bottom = `${constrainedBottom}px`
}

</script>

<style lang="scss">
.popover-palavra {
  user-select: none;
  position: fixed;
  bottom: 1em;
  right: 1em ;
  z-index: 1050;
  width: auto;
  opacity: 0.95;
  text-align: right;
  display: flex;
  flex-direction: column-reverse;
  justify-content: flex-end;
  align-items: flex-end;
  gap: 1px;

  &:hover {
    opacity: 1.0;
  }
  .arrow {
    position: absolute;
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-top: 10px solid #333;
    bottom: -10px;
    right: 20px;
  }
  .popover-header {
    background-color: #333;
    color: #999;
    padding: 0.1em 0.5em;
    position: relative;
    .popover-title {
      margin: 0;
      font-size: 1.1em;
      font-weight: bold;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5em;
    }
  }
  .popover-body {
    background-color: #222;
    padding: 10px;
  }

  .popover-individuo {
    border-radius: 10px;
    overflow: hidden;
    &.com_a_palavra {
      // min-width: 17em;
    }
    &.aparteante {
      margin-bottom: 1px;
      zoom: 0.75;
      display: inline-block;
      margin-right: 0.6em;
      .popover-body {
        background-color: #4e2f01;
      }
      .popover-header {
        background-color: #775201;
      }
    }
    .individuo-info {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1em;
      .info {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        .name {
          font-weight: bold;
          font-size: 1.1em;
          color: #999;
          text-align: left;
          small {
            font-weight: normal;
            font-size: 0.9em;
            margin-left: 5px;
          }
        }
      }
      .foto {
        width: 1.8em;
        height: 1.8em;
        background-size: cover;
        background-position: center;
        border-radius: 50%;
        background-color: #ccc;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8em;
        color: white;
        aspect-ratio: 1 / 1;
      }
      .info {
        flex: 2 1 100%;
        .role {
          font-size: 0.9em;
          color: #666;
        }
        .timer {
          font-size: 0.9em;
          color: #fff;
          font-weight: bold;
          .cron-popover-palavra {
            font-weight: bold;
            padding: 0 0.3em;
            .croncard {
              background-color: transparent;
              padding: 0;
              border: 0;
              box-shadow: none;
            }
          }
        }
      }
    }
  }
}
</style>
