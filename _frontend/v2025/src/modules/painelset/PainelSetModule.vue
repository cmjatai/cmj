<template>
  <div class="painelset-module">
    <div class="inner-painelset">
      <router-view />
    </div>
    <div
      id="painelset-editorarea"
      ref="painelsetEditorarea"
      @mousedown="initMoving($event)"
    />
  </div>
</template>
<script setup>
// 1. Imports

import { activeTeleportId } from '~@/stores/TeleportStore'
import { ref, watch, inject } from 'vue'

// 2. Composables
const EventBus = inject('EventBus')

// 3. Props & Emits

// 4. State & Refs
const painelsetEditorarea = ref(null)
const lastResizeWidth = ref('45%')
// 5. Computed Properties

// 6. Watchers
watch(
  () => activeTeleportId.value,
  (newTeleportId) => {
    painelsetEditorarea.value.style.flex = newTeleportId ? `0 0 ${lastResizeWidth.value}` : '0 0 0%'
  }
)

// 7. Events & Lifecycle Hooks
EventBus.on('painelset:editorarea:resize', (newWidth) => {
  painelsetEditorarea.value.style.flex = `0 0 ${newWidth}`
  if (['0', 0, '0%', '0px', '0em'].includes(newWidth)) {
    EventBus.emit('painelset:editorarea:close', 'force')
  }
})

const initMoving = (event) => {
  if (event.layerX > 3) {
    return
  }
  event.preventDefault()
  event.stopPropagation()

  console.debug(event)

  const startX = event.clientX
  const startWidth = painelsetEditorarea.value.offsetWidth

  const onMouseMove = (e) => {
    const newWidth = startWidth - (e.clientX - startX)
    lastResizeWidth.value = `${newWidth}px`
    painelsetEditorarea.value.style.flex = `0 0 ${lastResizeWidth.value}`
  }

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// 8. Functions

</script>
<style lang="scss" scoped>
  .painelset-module {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    flex-direction: row;
    gap: 0em;
    * {
      user-select: none;
    }
    .inner-painelset {
      display: flex;
      flex: 1 1 100%;
      flex-direction: column;
      z-index: 1;
    }
    #painelset-editorarea:not(:empty) {
      flex: 0 0 45%;
      padding: 5px;
    }
    #painelset-editorarea {
      position: relative;
      overflow: hidden;
      &::after {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 2px;
        border-left: 2px solid transparent;
        background-color: red;
        z-index: 1;
        cursor: col-resize;
      }
    }
  }
</style>
