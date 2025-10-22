<template>
  <div
    :id="`id-painelset-widget-${widgetSelected?.id}`"
    ref="painelsetWidget"
    :key="`painelset-widget-${widgetSelected?.id}`"
    :class="['painelset-widget', editmode ? 'editmode' : '']"
    :style="{ ...(widgetSelected?.styles.component || {}), ...styleDinamic, ...extra_styles }"
    @mousedown.stop.prevent="onMouseDown($event)"
    @click.stop.prevent="false"
  >
    <div
      v-if="widgetSelected?.config?.displayTitle"
      class="widget-titulo"
      :style="widgetSelected?.styles.title || {}"
    >
      {{ widgetSelected?.name }}
    </div>
    <div
      v-if="widgetSelected?.vue_component"
      class="inner-widget"
      :style="widgetSelected?.styles.inner || {}"
    >
      <component
        :is="widgetSelected?.vue_component"
        :painel-id="painelId"
        :widget-selected="widgetSelected?.id"
        @oncomponent="onComponent"
      />
    </div>
    <div
      v-if="!widgetSelected?.vue_component"
      class="inner-widget inner-children"
    >
      <Widget
        v-for="(widget, index) in childList"
        :key="`widget-${widget.id}-${index}`"
        :painel-id="painelId"
        :widget-selected="widget.id"
      />
    </div>
    <div
      v-if="editmode"
      class="manager"
    >
      <div class="position">
        {{ widgetSelected?.position }}
      </div>
      <div class="toolbar">
        <div class="btn-group ">
          <button
            class="btn btn-sm btn-danger"
            @mousedown.stop.prevent="false"
            @click.stop.prevent="onDeleteWidget($event)"
          >
            <FontAwesomeIcon :icon="'fa-solid fa-trash-can'" />
          </button>
          <button
            class="btn btn-sm btn-secondary"
            @mousedown.stop.prevent="false"
            @click.stop.prevent="onDuplicateWidget($event)"
          >
            <FontAwesomeIcon :icon="'fa-solid fa-clone'" />
          </button>
          <button
            class="btn btn-sm btn-primary"
            @mousedown.stop.prevent="false"
            @click.stop.prevent="addWidget($event)"
          >
            <FontAwesomeIcon :icon="'fa-solid fa-plus'" />
          </button>
        </div>
        <div class="btn-group right">
          <button
            class="btn btn-sm btn-dark"
            @mousedown.stop.prevent="false"
            @click.stop.prevent="openEditor($event)"
          >
            <FontAwesomeIcon icon="fa-solid fa-pen-to-square" />
          </button>
        </div>
      </div>
      <div
        class="resize-handle top-left"
        @mousedown="onMouseDownResize($event, 'top-left')"
      />
      <div
        class="resize-handle top-right"
        @mousedown="onMouseDownResize($event, 'top-right')"
      />
      <div
        class="resize-handle bottom-left"
        @mousedown="onMouseDownResize($event, 'bottom-left')"
      />
      <div
        class="resize-handle bottom-right"
        @mousedown="onMouseDownResize($event, 'bottom-right')"
      />
      <div
        class="resize-handle center-center"
        @mousedown="onMouseDownResize($event, 'center-center')"
      />
    </div>

    <Teleport
      v-if="widgetEditorOpened && editorActived"
      to="#painelset-editorarea"
      :disabled="!editorActived"
    >
      <WidgetEditor
        :painel-id="painelId"
        :widget-selected="widgetSelected?.id"
      />
    </Teleport>

    <!-- Teleport to="body">
      <Modal
        :show="widgetEditorOpened"
        @close="widgetEditorOpened = false"
      >
        <template #header>
          Edição do Widget: {{ widgetSelected?.name }}
        </template>
        <template #body>
          <WidgetEditor
            :painel-id="painelId"
            :widget-selected="widgetSelected?.id"
          />
        </template>
      </Modal>
    </!-->
  </div>
</template>

<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { activeTeleportId } from '~@/stores/teleportStore'

import { computed, ref, inject, watch, nextTick } from 'vue'
import Resource from '~@/utils/resources'
import WidgetEditor from './WidgetEditor.vue'

const syncStore = useSyncStore()

const EventBus = inject('EventBus')

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  }
})

const editmode = ref(false)
const painelsetWidget = ref(null)

const widgetEditorOpened = ref(false)
const extra_styles = ref({})
const coordsChange = ref({
  x: 0,
  y: 0,
  w: 100,
  h: 100,
  mouseResizeEnter: false
})

const editorActived = computed(() => {
  return painelsetWidget.value && activeTeleportId.value === painelsetWidget.value.id
})

const widgetSelected = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const styleDinamic = computed(() => {
  if (!widgetSelected.value || !widgetSelected.value.config?.coords) {
    return {}
  }
  const styles = {}
  const coords = widgetSelected.value.config.coords
  if (coords.x !== undefined) {
    styles.left = `${coords.x}%`
  }
  if (coords.y !== undefined) {
    styles.top = `${coords.y}%`
  }
  if (coords.w !== undefined) {
    styles.right = `${(coords.w + coords.x) > 100 ? 0 : 100 - (coords.w + coords.x)}%`
  }
  if (coords.h !== undefined) {
    styles.bottom = `${(coords.h + coords.y) > 100 ? 0 : 100 - (coords.h + coords.y)}%`
  }
  return styles
})

const childList = computed(() => {
  return _.orderBy(
    _.filter(syncStore.data_cache.painelset_widget, { parent: props.widgetSelected } ) || [],
    ['position'],
    ['asc']
  )
})

const syncChildList = async () => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'widget',
      filters: {
        parent: props.widgetSelected
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        // Process the fetched widgets
      }
    })
}

syncChildList()

EventBus.on('painelset:editorarea:close', (sender=null) => {
  if (sender && sender === 'force') {
    editmode.value = false
    widgetEditorOpened.value = false
    activeTeleportId.value = null
    return
  }
  if (sender && painelsetWidget.value && sender === painelsetWidget.value.id) {
    return
  }
  if (editmode.value) {
    return
  }
  editmode.value = false
  widgetEditorOpened.value = false
  activeTeleportId.value = null
})

watch(
  () => widgetEditorOpened.value,
  (newEditMode) => {
    if (newEditMode) {
      EventBus.emit('painelset:editorarea:close', painelsetWidget.value.id)
      nextTick(() => {
        activeTeleportId.value = painelsetWidget.value.id
      })
    } else {
      activeTeleportId.value = null
    }
  }
)

const onComponent = ((event) => {
  console.debug('Received oncomponent event:')
  if (!event || !event.type) {
    console.warn('Invalid oncomponent event received, missing type')
    return
  }
  if (event.type === 'extra_styles') {
    if (!event.extra_styles) {
      console.warn('Invalid extra_styles event, missing extra_styles data')
      return
    }
    const newStyles = {
      ...event.extra_styles
    }
    extra_styles.value = newStyles
  }
})
/* Edição do widget */

const openEditor = () => {
  console.debug('Opening widget editor modal for widget:', widgetSelected.value)
  widgetEditorOpened.value = !widgetEditorOpened.value
}

const onDeleteWidget = () => {
  if (!widgetSelected.value) {
    return
  }
  if (!confirm(`Confirma a exclusão do Widget: ${widgetSelected.value.name} e todos seus SubWidgets?`)) {
    return
  }
  Resource.Utils.deleteModel({
    app: 'painelset',
    model: 'widget',
    id: widgetSelected.value.id
  }).then(() => {
    console.log('Widget deleted successfully')
  }).catch((error) => {
    console.error('Error deleting widget:', error)
  })
}
const onDuplicateWidget = () => {
  if (!widgetSelected.value) {
    return
  }

  const newConfig = {
    ...widgetSelected.value.config,
    coords: {
      ...widgetSelected.value.config.coords,
      x: 10,
      y: 10
    }
  }

  const newWidgetData = {
    ...widgetSelected.value,
    id: undefined,
    name: `${widgetSelected.value.name} (Cópia)`,
    position: childList.value.length + 1,
    config: newConfig
  }

  Resource.Utils.createModel({
    app: 'painelset',
    model: 'widget',
    form: newWidgetData
  }).then((response) => {
    console.log('Widget duplicated successfully:', response.data)
  }).catch((error) => {
    console.error('Error duplicating widget:', error)
  })
}

const addWidget = () => {
  if (!widgetSelected.value) {
    return
  }

  const defaultChildWidgetData = {
    name: `Novo Widget`,
    parent: widgetSelected.value.id,
    visao: widgetSelected.value.visao,
    position: childList.value.length + 1,
    vue_component: '',
    config: {
      coords: {
        x: 10,
        y: 10,
        w: 30,
        h: 30
      },
      displayTitle: true
    },
    styles: {
      component: {},
      title: {},
      inner: {}
    }
  }

  Resource.Utils.createModel({
    app: 'painelset',
    model: 'widget',
    form: defaultChildWidgetData
  }).then((response) => {
    console.log('Default child widget created successfully:', response.data)
  }).catch((error) => {
    console.error('Error creating default child widget:', error)
  })
}

/* Helpers for resizing and moving widgets */

const validLocalCoords = (localCoords) => {
  if (!localCoords) {
    return false
  }
  if (localCoords.x === undefined ||
      localCoords.y === undefined ||
      localCoords.w === undefined ||
      localCoords.h === undefined ||
      localCoords.x === null ||
      localCoords.y === null ||
      localCoords.w === null ||
      localCoords.h === null
  ) {
    return false
  }
  if (localCoords.w > 5 && localCoords.w <= 100 &&
      localCoords.h > 5 && localCoords.h <= 100 &&
      localCoords.x >= 0 && localCoords.x <= 100 &&
      localCoords.y >= 0 && localCoords.y <= 100 &&
      (localCoords.x + localCoords.w) <= 100 &&
      (localCoords.y + localCoords.h) <= 100
  ) {
    return true
  }
  return false
}

const patchWidgetCoords = (localCoords) => {
  if (!validLocalCoords(localCoords)) {
    console.error('Invalid widget coordinates, aborting update')
    return
  }
  Resource.Utils.patchModel({
    app: 'painelset',
    model: 'widget',
    id: widgetSelected.value.id,
    form: {
      config: {
        ...widgetSelected.value.config,
        coords: {
          ...widgetSelected.value.config.coords,
          x: localCoords.x,
          y: localCoords.y,
          w: localCoords.w,
          h: localCoords.h
        }
      }
    }
  }).then((response) => {
    console.log(response.data)
    /* coordsChange.value.h = response.data.config.coords.h
    coordsChange.value.w = response.data.config.coords.w
    coordsChange.value.x = response.data.config.coords.x
    coordsChange.value.y = response.data.config.coords.y */
    console.log('Widget coordinates updated successfully')
  }).catch((error) => {
    console.error('Error updating widget coordinates:', error)
  })
}

const onMouseDown = (event) => {
  event.preventDefault()
  if (coordsChange.value.mouseResizeEnter) {
    return
  }
  editmode.value = !editmode.value
  if (!editmode.value) {
    widgetEditorOpened.value = false
  }
  console.log('Activating painel editor teleport for Widget:', props.widgetSelected)

  EventBus.emit('painelset:editorarea:close', painelsetWidget.value.id)
}

const onMouseDownResize = (event, direction) => {
  coordsChange.value.mouseResizeEnter = true
  event.preventDefault()
  if (!editmode.value) {
    return
  }

  // .resize-handle é o currentTarget, parent é .manager, parent é o widget em si
  // const currentTarget = event.currentTarget.parentElement.parentElement
  const currentTarget = painelsetWidget.value
  const widgetRect = currentTarget.getBoundingClientRect()
  const widgetParentRect = currentTarget.parentElement.getBoundingClientRect()

  const localCoords = { ...coordsChange.value }

  console.log('Mouse move detected:', event.clientX, event.clientY, widgetRect)

  const onMouseMove = (e) => {
    let newWidthPercent = 0
    let newHeightPercent = 0

    if (direction === 'top-left') {
      const newWidth = e.clientX - widgetRect.left
      const newHeight = e.clientY - widgetRect.top
      newWidthPercent = Math.round((newWidth / widgetParentRect.width) * 100)
      newHeightPercent = Math.round((newHeight / widgetParentRect.height) * 100)

      localCoords.w = widgetSelected.value.config.coords.w - newWidthPercent
      localCoords.h = widgetSelected.value.config.coords.h - newHeightPercent
      localCoords.x = widgetSelected.value.config.coords.x + newWidthPercent
      localCoords.y = widgetSelected.value.config.coords.y + newHeightPercent

    } else if (direction === 'top-right') {
      const newWidth = e.clientX - widgetRect.right
      const newHeight = e.clientY - widgetRect.top
      newWidthPercent = Math.round((newWidth / widgetParentRect.width) * 100)
      newHeightPercent = Math.round((newHeight / widgetParentRect.height) * 100)

      localCoords.w = widgetSelected.value.config.coords.w + newWidthPercent
      localCoords.h = widgetSelected.value.config.coords.h - newHeightPercent
      localCoords.x = widgetSelected.value.config.coords.x
      localCoords.y = widgetSelected.value.config.coords.y + newHeightPercent

    } else if (direction === 'bottom-right') {
      const newWidth = e.clientX - widgetRect.right
      const newHeight = e.clientY - widgetRect.bottom
      newWidthPercent = Math.round((newWidth / widgetParentRect.width) * 100)
      newHeightPercent = Math.round((newHeight / widgetParentRect.height) * 100)

      localCoords.w = widgetSelected.value.config.coords.w + newWidthPercent
      localCoords.h = widgetSelected.value.config.coords.h + newHeightPercent
      localCoords.x = widgetSelected.value.config.coords.x
      localCoords.y = widgetSelected.value.config.coords.y

    } else if (direction === 'bottom-left') {
      const newWidth = e.clientX - widgetRect.left
      const newHeight = e.clientY - widgetRect.bottom
      newWidthPercent = Math.round((newWidth / widgetParentRect.width) * 100)
      newHeightPercent = Math.round((newHeight / widgetParentRect.height) * 100)

      localCoords.w = widgetSelected.value.config.coords.w - newWidthPercent
      localCoords.h = widgetSelected.value.config.coords.h + newHeightPercent
      localCoords.x = widgetSelected.value.config.coords.x + newWidthPercent
      localCoords.y = widgetSelected.value.config.coords.y

    } else if (direction === 'center-center') {
      const deltaX = e.clientX - widgetRect.left - (widgetRect.width / 2)
      const deltaY = e.clientY - widgetRect.top - (widgetRect.height / 2)
      newWidthPercent = Math.round((deltaX / widgetParentRect.width) * 100)
      newHeightPercent = Math.round((deltaY / widgetParentRect.height) * 100)
      console.debug('Resizing widget...', deltaX, deltaY, direction, newWidthPercent, newHeightPercent, localCoords)

      localCoords.w = widgetSelected.value.config.coords.w
      localCoords.h = widgetSelected.value.config.coords.h
      localCoords.x = widgetSelected.value.config.coords.x + newWidthPercent
      localCoords.y = widgetSelected.value.config.coords.y + newHeightPercent
    }

    console.debug('Resizing widget...', e.clientX, e.clientY, direction, newWidthPercent, newHeightPercent, localCoords)

    if (validLocalCoords(localCoords)) {
      coordsChange.value.w = localCoords.w
      coordsChange.value.h = localCoords.h
      coordsChange.value.x = localCoords.x
      coordsChange.value.y = localCoords.y

      currentTarget.style.right = `${100 - (localCoords.w + localCoords.x)}%`
      currentTarget.style.bottom = `${100 - (localCoords.h + localCoords.y)}%`
      currentTarget.style.left = `${localCoords.x}%`
      currentTarget.style.top = `${localCoords.y}%`
    } else {
      console.warn('Invalid coordinates during resize, ignoring update')
    }
  }
  console.log('Starting resize operation')
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', (e) => {
    window.removeEventListener('mouseup', this)
    window.removeEventListener('mousemove', onMouseMove)
    e.preventDefault()
    if (!coordsChange.value.mouseResizeEnter) {
      return
    }
    coordsChange.value.mouseResizeEnter = false
    patchWidgetCoords({
      x: coordsChange.value.x,
      y: coordsChange.value.y,
      w: coordsChange.value.w,
      h: coordsChange.value.h
    })
    console.log('Resize operation ended')
  })
}
</script>

<style lang="scss" scoped>
  .painelset-widget {
    position: absolute;
    display: flex;
    flex-direction: column;
    flex: 1 1 100%;
    z-index: 1;
    overflow: hidden;
    border: 0;
    .inner-widget {
      position: relative;
      display: flex;
      justify-content: center;
      overflow: hidden;
      flex-direction: column;
      flex: 1 1 100%;
      z-index: 1;
    }
    & > .resize-handle {
      display: none;
    }
    &.localize {
      border: 2px dashed red ;
    }
    &.editmode {
      border: 2px dashed yellow;
      z-index: 10;
      &::before {
        content: '';
        position: absolute;
        top: 0px;
        left: 0px;
        width: 100%;
        height: 100%;
        font-size: 0.8em;
        // linear gradient diagonal stripes
        background-image: repeating-linear-gradient(
          45deg,
          rgba(0, 0, 0, 0.2),
          rgba(0, 0, 0, 0.2) 10px,
          rgba(0, 0, 0, 0.25) 10px,
          rgba(0, 0, 0, 0.25) 25px
        );
        z-index: -1;
      }
      & > .manager {
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 1;

        .position {
          position: absolute;
          top: 10px;
          left: 10px;
          background-color: rgba(0, 0, 0, 1);
          color: #fff;
          opacity: 0.2;
          padding: 2px 15px;
          font-size: 20pt;
          border-radius: 3px;
          z-index: 10003;
          &:hover {
            opacity: 1;
          }
        }

        & > .toolbar {
          position: absolute;
          left: 10px;
          bottom: 10px;
          right: 10px;
          display: flex;
          justify-content: flex-end;
          gap: 5px;
          z-index: 1002;
        }

        & > .resize-handle {
          position: absolute;
          display: block;
          width: 10px;
          height: 10px;
          background-color: #fff;
          z-index: 1001;
          &.top-left {
            top: -1px;
            left: -1px;
            cursor: nw-resize;
          }
          &.top-right {
            top: -1px;
            right: -1px;
            cursor: ne-resize;
          }
          &.bottom-left {
            bottom: -1px;
            left: -1px;
            cursor: sw-resize;
          }
          &.bottom-right {
            bottom: -1px;
            right: -1px;
            cursor: se-resize;
          }
          &.center-center {
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              width: 25px;
              height: 25px;
              background-color: transparent;
              cursor: move;

              &::before,
              &::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 25px;
                height: 5px;
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
              }

              &::before {
              transform: translate(-50%, -50%) rotate(45deg);
              }

              &::after {
              transform: translate(-50%, -50%) rotate(-45deg);
              }
          }
        }
      }
    }

  }
</style>
