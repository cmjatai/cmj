<template>
  <div
    :id="`id-painelset-visaodepainel${visaodepainelSelected}`"
    ref="painelsetVisaodepainel"
    :key="`painelset-visaodepainel${visaodepainelSelected}`"
    class="painelset-visaodepainel"
    :style="visaoDePainelSelected?.styles.component || {}"
  >
    <div
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
    <div
      v-if="widgetList.length === 0"
      class="visao-empty"
    >
      <p>Não há widgets configurados para esta visão.</p>
      <p>Utilize o botao de adição na tela de configurações para adicionar o primeiro widget à visão.</p>
    </div>
    <Teleport
      v-if="editmode"
      to="#painelset-editorarea"
      :disabled="!editmode"
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
import { useAuthStore } from '~@/stores/AuthStore'
import { activeTeleportId } from '~@/stores/TeleportStore'

import { ref, defineProps, computed, watch, inject, nextTick } from 'vue'

import Widget from './Widget.vue'
import VisaoEditor from './editors/VisaoEditor.vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  visaodepainelSelected: {
    type: Number,
    default: 0
  },
  editmodeVisao: {
    type: Boolean,
    default: false
  }
})

const EventBus = inject('EventBus')
const editmode = ref(props.editmodeVisao)
const painelsetVisaodepainel = ref(null)

const onChangePermission = () => {
  if (!authStore.isAuthenticated) {
    return false
  }
  return authStore.hasPermission('painelset.change_visaodepainel')
}

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
watch(
  () => props.editmodeVisao,
  (newEditMode) => {
    editmode.value = newEditMode
    if (newEditMode) {
      activeTeleportId.value = painelsetVisaodepainel.value.id
    }
  }
)

const syncWidgetList = async () => {
  syncStore
    .fetchSync({
      app: 'painelset',
      model: 'widget',
      params: {
        visao: props.visaodepainelSelected,
        get_all: 'True'
      }
    })
    .then((response) => {
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
