<template>
  <div
    class="doclist-layout container-fluid"
    v-if="classe"
  >
    <BreadCrumbClasse :parents="classe.parents" />
    <div class="row-fluid">
      <div class="col">
        <h2>{{ classe.titulo }}</h2>
        <small v-html="descricaoHtml" />
        <div class="inner-list">
          <ArqDocItem
            :arqdoc="doc"
            :classe="classe"
            v-for="(doc, k) in arqdocsOrdered"
            :key="`ad-${k}`"
          />
        </div>
        <div class="text-info">
          TODO: implementar paginação
        </div>
      </div>
      <div class="col-3 d-none">
        <div class="classechild">
          <h4>Subclasses de {{ classe.titulo }}</h4>
          {{ paramsNode }} - {{ paramsNodechild }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import { addArrayOfIds } from '~@/utils/storageArray'
import ArqDocItem from './ArqDocItem.vue'
import BreadCrumbClasse from './BreadCrumbClasse.vue'

const route = useRoute()
const messageStore = useMessageStore()

const ARQCLASSE_FISICA = 100

const paramsNode = ref(route.params.node)
const paramsNodechild = ref(route.params.nodechild)
const classe = ref(null)
const nodeKeyLocalstorage = 'portalcmj_arqnode_tree_opened'
const arqdocs = ref({})

const emit = defineEmits(['checkIsOpenedNodesTree'])

const arqdocsOrdered = computed(() => {
  return [...Object.values(arqdocs.value)].sort((a, b) => b.id - a.id)
})

const descricaoHtml = computed(() => {
  if (!classe.value) return ''
  let descr = classe.value.descricao
  descr = descr.replace(/\r\n/g, '<br>')
  descr = descr.replace(/\n/g, '<br>')
  return descr
})

function fetchDocs (page = 1, queryString = '') {
  arqdocs.value = {}
  return Resources.Utils.fetch({
    app: 'arq',
    model: 'arqdoc',
    query_string: `o=-data&page=${page}${queryString}`
  })
    .then((response) => {
      const data = Array.isArray(response.data) ? response.data : (response.data.results || response.data)
      data.forEach((item) => {
        arqdocs.value[item.id] = item
      })
    })
    .catch(() => {
      messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar os documentos...', timeout: 5000 })
    })
}

function fetchClasse () {
  if (paramsNodechild.value === 'root') return Promise.resolve(null)

  return Resources.Utils.fetch({
    app: 'arq',
    model: 'arqclasse',
    id: paramsNodechild.value
  })
    .then((response) => {
      classe.value = response.data
      return response.data
    })
    .catch(() => {
      messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar classe selecionada...', timeout: 5000 })
    })
}

onMounted(async () => {
  await fetchClasse()
  if (!classe.value) return
  classe.value.parents.forEach((item) => {
    addArrayOfIds(nodeKeyLocalstorage, item.id)
  })
  emit('checkIsOpenedNodesTree')
  const fieldClasse = classe.value.perfil === ARQCLASSE_FISICA ? 'classe_estrutural' : 'classe_logica'
  fetchDocs(1, `&get_all=True&${fieldClasse}=${classe.value.id}`)
})

defineExpose({ classe })
</script>

<style lang="scss">
.container-arqtree {
  .doclist-layout {
    position: sticky;
    top: 0;
    z-index: 1;
    .inner-list {
      border: 1px solid #eee;
      margin: 15px 0;
      background-color: white;
    }
  }
  .row, .col-3 {
    position: relative;
  }
  .col-3 {
    border-left: 1px solid #ccc;
  }
  .classechild {
    position: sticky;
    display: block;
    top: 0;
  }
}
</style>
