<template>
  <div
    ref="painelsetWidgetEditor"
    :key="`painelset-widget-editor-${widgetSelected?.id}`"
    class="painelset-widget-editor"
  >
    <form
      action=""
      @change="changeForm($event)"
    >
      <fieldset>
        <legend>Configurações do Widget</legend>
        <div class="container">
          <div class="row py-2">
            <div class="col-3 py-2">
              <div class="form-group">
                <div
                  id="div_id_display_title"
                  class="custom-control custom-checkbox"
                >
                  <input
                    type="checkbox"
                    name="display_title"
                    class="checkboxinput custom-control-input"
                    aria-describedby="id_display_title_helptext"
                    v-model="widgetSelected.config.displayTitle"
                    id="id_display_title"
                  >&nbsp;
                  <label
                    for="id_display_title"
                    class="custom-control-label"
                  >
                    Mostrar título do widget?
                  </label><br>
                  <small
                    id="hint_id_display_title"
                    class="form-text text-muted"
                  >
                    Ativa/Desativa exibição do título
                  </small>
                </div>
              </div>
            </div>
            <div
              class="col-3"
              v-if="childList.length === 0"
            >
              <label
                for="widget-vue-component"
                class="form-label"
              >Componente Vue</label>
              <select
                class="form-select"
                v-model="widgetSelected.vue_component"
                id="widget-vue-component"
              >
                <option
                  v-for="(label, componentName) in vueComponentsChoice"
                  :key="`widget-vue-component-option-${componentName}`"
                  :value="componentName"
                >
                  {{ label }}
                </option>
              </select>
            </div>
            <div class="col-6">
              <label
                for="widget-name"
                class="form-label"
              >Título do Widget</label>
              <input
                type="text"
                class="form-control"
                v-model="widgetSelected.name"
                placeholder="Título do Widget"
              >
            </div>
          </div>
          <div class="row py-2">
            <div class="col-6">
              <div
                id="div_id_config"
                class="form-group"
              >
                <label
                  for="widget-config"
                  class="form-label"
                >Configurações do Widget (JSON)</label>
                <div>
                  <textarea
                    id="widget-config"
                    name="config"
                    class="form-control"
                    v-model="jsonValues.config"
                    placeholder="Configurações do Widget em JSON"
                    rows="15"
                    @blur="changeJsonValues"
                  />
                </div>
              </div>
            </div>
            <div class="col-6">
              <div
                id="div_id_styles"
                class="form-group"
              >
                <label
                  for="widget-styles"
                  class="form-label"
                >Estilos do Widget (JSON)</label>
                <div>
                  <textarea
                    name="styles"
                    id="widget-styles"
                    class="form-control"
                    v-model="jsonValues.styles"
                    rows="15"
                    placeholder="Estilos do Widget em JSON"
                    @blur="changeJsonValues"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="container">
          <div class="row">
            <div class="col-12">
              <div
                id="div_id_description"
                class="form-group"
              >
                <label
                  for="id_description"
                  class="form-label"
                >Descrição do Widget</label>
                <div>
                  <textarea
                    id="id_description"
                    name="description"
                    class="form-control"
                    v-model="widgetSelected.description"
                    placeholder="Descrição do Widget"
                    rows="5"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="container actions pt-3">
          <div class="row">
            <div class="col-12">
              <div class="btn-group">
                <button
                  class="btn btn-secondary"
                  @click.stop.prevent="closeEditor($event)"
                  title="Fechar Editor de Widget"
                >
                  <FontAwesomeIcon :icon="['fas', 'times']" />
                </button>
                <button
                  class="btn btn-sm btn-danger"
                  @mousedown.stop.prevent="false"
                  @click.stop.prevent="onDeleteWidget($event)"
                >
                  <FontAwesomeIcon :icon="'fa-solid fa-trash-can'" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </fieldset>
    </form>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '../../messages/store/MessageStore'
import { computed, ref, watch, inject } from 'vue'

import Resource from '~@/utils/resources'

const painelsetWidgetEditor = ref(null)

const syncStore = useSyncStore()
const messageStore = useMessageStore()

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

const vueComponentsChoice = ref({
  '': 'Nenhum componente selecionado',
  'WidgetSessaoPlenariaTitulo': 'WidgetSessaoPlenariaTitulo - Título da Sessão Plenária vinculada ao Painel',
  'WidgetCronometroEvento': 'WidgetCronometroEvento - Cronômetro do Evento vinculado ao Painel',
  'WidgetCronometroPalavra': 'WidgetCronometroPalavra - Cronômetro da Palavra vinculada ao Painel'
})

const widgetSelected = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const childList = computed(() => {
  return _.orderBy(
    _.filter(syncStore.data_cache.painelset_widget, { parent: props.widgetSelected } ) || [],
    ['position'],
    ['asc']
  )
})

const jsonConfig = computed(() => {
  if (!widgetSelected.value || !widgetSelected.value.config) {
    return ''
  }
  return JSON.stringify(widgetSelected.value.config, null, 2)
})

const jsonStyles = computed(() => {
  if (!widgetSelected.value || !widgetSelected.value.styles) {
    return ''
  }
  return JSON.stringify({
    component: widgetSelected.value.styles.component || {},
    title: widgetSelected.value.styles.title || {},
    inner: widgetSelected.value.styles.inner || {}
  }, null, 2)
})

const jsonValues = ref({
  config: jsonConfig.value,
  styles: jsonStyles.value
})

// Function to handle

const closeEditor = (event) => {
  EventBus.emit('painelset:editorarea:close')
  EventBus.emit('painelset:editorarea:resize', 0)
}

const changeJsonValues = () => {
  if (!widgetSelected.value) {
    return
  }
  try {
    const parsedConfig = JSON.parse(jsonValues.value.config)
    const parsedStyles = JSON.parse(jsonValues.value.styles)
    widgetSelected.value.styles = parsedStyles
    widgetSelected.value.config = parsedConfig
    jsonValues.value.config = JSON.stringify(parsedConfig, null, 2)
    jsonValues.value.styles = JSON.stringify(parsedStyles, null, 2)
    patchModel({
      config: parsedConfig,
      styles: parsedStyles
    })
  } catch (e) {
    messageStore.addMessage({
      type: 'danger',
      text: `Erro ao atualizar os campos JSON: ${e.message}`,
      timeout: 10000
    })
    console.error('Erro ao atualizar os campos JSON:', e)
    jsonValues.value.config = jsonConfig.value
    jsonValues.value.styles = jsonStyles.value
  }
}

const changeForm = (event) => {
  console.log('WidgetEditor.vue: changeForm event:', event)
  const nnv = {...widgetSelected.value}
  delete nnv.id

  if (vueComponentsChoice.value[nnv.vue_component] === undefined) {
    nnv.vue_component = ''
  }
  if (!['styles', 'config'].includes(event.target.name)) {
    patchModel(nnv)
  }
}

const patchModel = async (modelData) => {
  try {
    await Resource.Utils.patchModel({
      app: 'painelset',
      model: 'widget',
      id: widgetSelected.value.id,
      form: modelData
    })
    messageStore.addMessage({
      type: 'info',
      text: 'Widget atualizado.',
      timeout: 2000
    })
    console.log('WidgetEditor.vue: patchModel updated successfully.')
  } catch (error) {
    messageStore.addMessage({
      type: 'danger',
      text: 'Erro ao salvar as alterações do Widget.',
      timeout: 5000
    })
    console.error('Erro ao salvar as alterações do Widget:', error)
  }
}

watch(
  () => widgetSelected.value,
  (newVal) => {
    if (newVal) {
      jsonValues.value.config = jsonConfig.value
      jsonValues.value.styles = jsonStyles.value
    }
  }
)

const onDeleteWidget = (event) => {
  if (!widgetSelected.value) {
    return
  }
  if (!confirm(`Confirma a exclusão do Widget: ${widgetSelected.value.name} ?`)) {
    return
  }
  Resource.Utils.deleteModel({
    app: 'painelset',
    model: 'widget',
    id: widgetSelected.value.id
  }).then(() => {
    console.log('Widget deleted successfully')
    EventBus.emit('painelset:editorarea:close', 'force')
  }).catch((error) => {
    console.error('Error deleting widget:', error)
  })
}
</script>

<style lang="scss" scoped>
.painelset-widget-editor {
  * {
    user-select: text !important;
  }
  #widget-config,
  #widget-styles {
    height: 100%;
    font-family: monospace;
  }
  height: 100%;
}
</style>
