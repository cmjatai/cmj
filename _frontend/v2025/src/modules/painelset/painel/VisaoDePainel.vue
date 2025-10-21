<template>
  <div
    :id="`id-painelset-visaodepainel${visaodepainelSelected}`"
    ref="painelsetVisaodepainel"
    :key="`painelset-visaodepainel${visaodepainelSelected}`"
    class="painelset-visaodepainel"
    :style="visaoDePainelSelected?.styles.component || {}"
    @click.stop="editmode = !editmode"
  >
    <div
      v-if="visaoDePainelSelected?.config?.displayTitle"
      class="visaodepainel-titulo"
      :style="visaoDePainelSelected?.styles.title || {}"
    >
      {{ visaoDePainelSelected?.name }}
    </div>
    <div
      class="inner-visaodepainel"
      :style="visaoDePainelSelected?.styles.inner || {}"
    >
      <Widget
        v-for="(widget, index) in widgetList"
        :key="`widget-${widget.id}-${index}`"
        :painel-id="painelId"
        :widget-selected="widget.id"
      />
    </div>
    <div v-if="widgetList.length === 0" class="visao-empty">
      <p>Não há widgets configurados para esta visão.</p>
      <p>Utilize o botao de adição na tela de configurações para adicionar o primeiro widget à visão.</p>
    </div>
    <Teleport
      v-if="editmode && editorActived"
      to="#painelset-editorarea"
      :disabled="!editorActived"
    >
      <VisaoEditor
        :painel-id="painelId"
        :visao-selected="visaodepainelSelected"
      />
    </Teleport>

  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { activeTeleportId } from '~@/stores/teleportStore'

import { ref, defineProps, computed, watch, inject, nextTick } from 'vue'

import Widget from './Widget.vue'
import VisaoEditor from './VisaoEditor.vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  visaodepainelSelected: {
    type: Number,
    default: 0
  }
})

const EventBus = inject('EventBus')
const editmode = ref(false)
const painelsetVisaodepainel = ref(null)

const editorActived = computed(() => {
  return activeTeleportId.value === painelsetVisaodepainel.value.id
})

EventBus.on('painelset:editorarea:close', (sender=null) => {
  if (sender && sender === 'force') {
    editmode.value = false
    activeTeleportId.value = null
    return
  }

  if (sender && painelsetVisaodepainel.value && sender ===  painelsetVisaodepainel.value.id) {
    return
  }
  activeTeleportId.value = null
  editmode.value = false
})

watch(
  () => editmode.value,
  (newEditMode) => {
    if (newEditMode) {
      EventBus.emit('painelset:editorarea:close', painelsetVisaodepainel.value.id)
      nextTick(() => {
        activeTeleportId.value = painelsetVisaodepainel.value.id
      })

    } else {
      activeTeleportId.value = null
    }
  }
)
const visaoDePainelSelected = computed(() => {
  return syncStore.data_cache.painelset_visaodepainel?.[props.visaodepainelSelected] || null
})

const widgetList = computed(() => {
  return _.orderBy(
    _.filter(
      syncStore.data_cache.painelset_widget,
      { visao: props.visaodepainelSelected, parent: null }
    ) || [],
    ['position'],
    ['asc']
  )
})

const syncWidgetList = async () => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'widget',
      filters: {
        visaodepainel: props.visaodepainelSelected
      }
    })
    .then((response) => {
      if (response && response.data.results.length > 0) {
        // Process the fetched widgets
      }
    })
}

syncWidgetList()

</script>

<style lang="scss" scoped>
  .painelset-visaodepainel {
    display: flex;
    flex-direction: column;
    flex: 1 1 100%;
    .inner-visaodepainel {
      position: relative;
      flex-direction: column;
      flex: 1 1 100%;
    }
    & > .visao-empty {
      flex: 1 1 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: #888;
      font-size: 1.2em;
      text-align: center;
      padding: 1em;
    }
  }
</style>
