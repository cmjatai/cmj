<template>
  <div
    ref="painelsetVisaoEditor"
    :key="`painelset-visaodepainel-editor-${visaoSelected?.id}`"
    class="painelset-visaodepainel-editor"
  >
    <form
      action=""
      @change="changeForm($event)"
    >
      <fieldset>
        <legend>Configurações da Visão do Painel</legend>
        <div class="container">
          <div class="row py-2">
            <div class="col-6">
              <label
                for="painel-name"
                class="form-label"
              >Título da Visão do Painel</label>
              <input
                type="text"
                class="form-control"
                v-model="visaoSelected.name"
                placeholder="Título da Visão do Painel"
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
                  for="painel-config"
                  class="form-label"
                >Configurações da Visão do Painel (YAML)</label>
                <div>
                  <textarea
                    id="painel-config"
                    name="config"
                    class="form-control"
                    v-model="yamlValues.config"
                    placeholder="Configurações da Visão do Painel em YAML"
                    rows="15"
                    @blur="changeYamlValues"
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
                  for="painel-styles"
                  class="form-label"
                >Estilos da Visão do Painel (YAML)</label>
                <div>
                  <textarea
                    name="styles"
                    id="painel-styles"
                    class="form-control"
                    v-model="yamlValues.styles"
                    rows="15"
                    placeholder="Estilos da Visão do Painel em YAML"
                    @blur="changeYamlValues"
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
                >Descrição do Painel</label>
                <div>
                  <textarea
                    id="id_description"
                    name="description"
                    class="form-control"
                    v-model="visaoSelected.description"
                    placeholder="Descrição do Painel"
                    rows="5"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="container actions pt-3">
          <div class="row">
            <div class="col-12 d-flex gap-2">
              <div class="btn-group">
                <button
                  class="btn btn-secondary"
                  @click.stop.prevent="closeEditor($event)"
                  title="Fechar Editor da Visão do Painel"
                >
                  <FontAwesomeIcon :icon="['fas', 'times']" />
                </button>
                <button
                  class="btn btn-danger"
                  @mousedown.stop.prevent="false"
                  @click.stop.prevent="onDeleteVisaodepainel($event)"
                  title="Excluir Visão do Painel"
                >
                  <FontAwesomeIcon :icon="'fa-solid fa-trash-can'" />
                </button>
              </div>

              <div class="btn-group">
                <button
                  class="btn btn-primary"
                  @mousedown.stop.prevent="false"
                  @click.stop.prevent="addWidget($event)"
                  title="Adicionar Widget à Visão do Painel"
                >
                  <FontAwesomeIcon :icon="'fa-solid fa-plus'" />
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
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import { computed, ref, watch, inject } from 'vue'

import YAML from 'js-yaml'
import Resource from '~@/utils/resources'

const EventBus = inject('EventBus')

const painelsetVisaoEditor = ref(null)

const syncStore = useSyncStore()
const messageStore = useMessageStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  visaoSelected: {
    type: Number,
    default: 0
  }
})

const visaoSelected = computed(() => {
  return syncStore.data_cache.painelset_visaodepainel?.[props.visaoSelected] || null
})

const yamlConfig = computed(() => {
  if (!visaoSelected.value || !visaoSelected.value.config) {
    return ''
  }
  return YAML.dump(visaoSelected.value.config)
})

const yamlStyles = computed(() => {
  if (!visaoSelected.value || !visaoSelected.value.styles) {
    return ''
  }
  return YAML.dump({
    component: visaoSelected.value.styles.component || {},
    title: visaoSelected.value.styles.title || {display: 'flex'},
    inner: visaoSelected.value.styles.inner || {}
  })
})

const yamlValues = ref({
  config: yamlConfig.value,
  styles: yamlStyles.value
})

const changeYamlValues = () => {
  if (!visaoSelected.value) {
    return
  }
  try {
    const parsedConfig = yamlValues.value.config ? YAML.load(yamlValues.value.config) : {}
    const parsedStyles = yamlValues.value.styles ? YAML.load(yamlValues.value.styles) : {}
    visaoSelected.value.styles = parsedStyles
    visaoSelected.value.config = parsedConfig
    yamlValues.value.config = YAML.dump(parsedConfig)
    yamlValues.value.styles = YAML.dump(parsedStyles)
    patchModel({
      config: parsedConfig,
      styles: parsedStyles
    })
  } catch (e) {
    messageStore.addMessage({
      type: 'danger',
      text: `Erro ao atualizar os campos YAML: ${e.message}`,
      timeout: 10000
    })
    console.error('Erro ao atualizar os campos YAML:', e)
    yamlValues.value.config = yamlConfig.value
    yamlValues.value.styles = yamlStyles.value
  }
}

const changeForm = (event) => {
  console.log('VisaoEditor.vue: changeForm event:', event)
  const nnv = {...visaoSelected.value}
  delete nnv.id

  if (!['styles', 'config'].includes(event.target.name)) {
    patchModel(nnv)
  }
}

const patchModel = async (modelData) => {
  try {
    await Resource.Utils.patchModel({
      app: 'painelset',
      model: 'visaodepainel',
      id: visaoSelected.value.id,
      form: modelData
    })
    messageStore.addMessage({
      type: 'info',
      text: 'Visão do Painel atualizado.',
      timeout: 2000
    })
    console.log('VisaoEditor.vue: patchModel updated successfully.')
  } catch (error) {
    messageStore.addMessage({
      type: 'danger',
      text: 'Erro ao salvar as alterações do Visão do Painel.',
      timeout: 5000
    })
    console.error('Erro ao salvar as alterações do Visão do Painel:', error)
  }
}

watch(
  () => visaoSelected.value,
  (newVal) => {
    if (newVal) {
      yamlValues.value.config = yamlConfig.value
      yamlValues.value.styles = yamlStyles.value
    }
  }
)

const closeEditor = (event) => {
  EventBus.emit('painelset:editorarea:close')
  EventBus.emit('painelset:editorarea:resize', 0)
}
const onDeleteVisaodepainel = () => {
  if (!visaoSelected.value) {
    return
  }
  if (!confirm(`Confirma a exclusão da Visão do Painel: ${visaoSelected.value.name} ?`)) {
    return
  }
  Resource.Utils.deleteModel({
    app: 'painelset',
    model: 'visaodepainel',
    id: visaoSelected.value.id
  })
  .then(() => {
    messageStore.addMessage({
      type: 'info',
      text: 'Visão do Painel excluído com sucesso.',
      timeout: 5000
    })
    EventBus.emit('painelset:editorarea:close', 'force')
  })
  .catch((error) => {
    messageStore.addMessage({
      type: 'danger',
      text: 'Erro ao excluir a Visão do Painel.',
      timeout: 5000
    })
    console.error('Error deleting visaodepainel:', error)
  })
}

const addWidget = () => {
  if (!visaoSelected.value) {
    return
  }

  const defaultChildWidgetData = {
    name: 'Novo Widget',
    parent: null,
    visao: visaoSelected.value.id,
    position: syncStore.data_cache.painelset_widget
      ? Object.values(syncStore.data_cache.painelset_widget)
        .filter(w => w.visao === visaoSelected.value.id).length + 1
      : 1,
    vue_component: '',
    config: {
      coords: {
        x: 10,
        y: 10,
        w: 30,
        h: 30
      }
    },
    styles: {
      component: {},
      title: {display: 'flex'},
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
</script>

<style lang="scss" scoped>
.painelset-visaodepainel-editor {
  * {
    user-select: text !important;
  }
  #painel-config,
  #painel-styles {
    height: 100%;
    font-family: monospace;
  }
  height: 100%;

}
</style>
