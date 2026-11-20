<template>
  <div
    :class="[
      'node-element',
      node !== null && node.count_childs === 0 ? 'type-content' : '',
      node !== null && node.id === parseInt(nodechild_params) ? 'active' : ''
    ]"
  >
    <div
      :class="['node-titulo', `level-${level}`]"
      v-if="node"
    >
      <span class="spacer" />
      <span
        class="toggle"
        v-if="node.count_childs !== 0"
        @click="clickToggle"
      >
        <FontAwesomeIcon
          v-if="!is_opened || !hasChilds"
          icon="chevron-right"
        />
        <FontAwesomeIcon
          v-if="is_opened && hasChilds"
          icon="chevron-down"
        />
      </span>
      <span class="content">
        <router-link
          :to="{ name: 'arqchildroute', params: { node: node_params, nodechild: node.id } }"
          @click="clickRoute"
        >
          {{ node.titulo }}
          <FontAwesomeIcon
            v-if="node.checkcheck"
            icon="lock"
            size="xs"
            class="text-light-blue"
            title="ArqClasse Arquivada."
          />
        </router-link>
        <div class="btn-group btn-group-sm el-actions">
          <a
            :href="`/arqadmin/classe/${node.id}`"
            target="_blank"
            class="btn btn-link"
          >
            <FontAwesomeIcon icon="edit" />
          </a>
          <a
            :href="`/arq/${node.id}/${node.id}`"
            class="btn btn-link"
          >
            <FontAwesomeIcon icon="expand" />
          </a>
        </div>
        <small
          class="box-descricao"
          v-html="descricaoHtml"
        />
      </span>
    </div>
    <NodeLayout
      :elemento="raiz"
      :parent="elemento"
      :level="level + 1"
      v-for="(raiz, k) in childs"
      :key="`class-${k}`"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import { addArrayOfIds, delItemArrayOfIds, inArrayOfIds } from '~@/utils/storageArray'

const route = useRoute()
const messageStore = useMessageStore()

const props = defineProps({
  parent: { type: Object, default: null },
  elemento: { type: Object, default: undefined },
  level: { type: Number, required: true }
})

const childs = ref({})
const is_opened = ref(false)
const node_params = ref(route.params.node)
const nodechild_params = ref(route.params.nodechild)
const node = ref(null)
const nodeKeyLocalstorage = 'portalcmj_arqnode_tree_opened'

const hasChilds = computed(() => Object.keys(childs.value).length > 0)

const descricaoHtml = computed(() => {
  if (!node.value) return ''
  let descr = node.value.descricao
  descr = descr.replace(/\r\n/g, '<br>')
  descr = descr.replace(/\n/g, '<br>')
  return `<strong>${node.value.conta}</strong> - <strong>${node.value.titulo}</strong><br><i>${descr}</i>`
})

watch(is_opened, (nv) => {
  if (nv) {
    fetchList(1, `&get_all=True&parent=${node.value.id}`)
    addArrayOfIds(nodeKeyLocalstorage, node.value.id)
  } else {
    childs.value = {}
    if (node.value) {
      delItemArrayOfIds(nodeKeyLocalstorage, node.value.id)
    }
  }
})

watch(route, () => {
  node_params.value = route.params.node
  nodechild_params.value = route.params.nodechild
  nextTick(() => {
    openIfInArrayOfIds()
  })
})

function clickRoute () {
  clickToggle()
}

function clickToggle () {
  is_opened.value = !is_opened.value
}

function openIfInArrayOfIds () {
  if (node.value && !is_opened.value && inArrayOfIds(nodeKeyLocalstorage, node.value.id)) {
    is_opened.value = true
    fetchList(1, `&get_all=True&parent=${node.value.id}`)
  }
}

function reload () {
  node.value = props.elemento || null
  if (node_params.value === 'root' && props.elemento === undefined) {
    fetchList(1, '&get_all=True&parent__isnull=True')
  } else if (props.elemento === undefined) {
    fetchElemento(node_params.value)
      .then(() => {
        fetchList(1, `&get_all=True&parent=${node_params.value}`)
          .then(() => {
            clickToggle()
          })
      })
  } else {
    openIfInArrayOfIds()
  }
}

function fetchList (page = 1, queryString = '') {
  childs.value = {}
  return Resources.Utils.fetch({
    app: 'arq',
    model: 'arqclasse',
    query_string: `o=titulo&page=${page}${queryString}`
  })
    .then((response) => {
      const data = Array.isArray(response.data) ? response.data : (response.data.results || response.data)
      data.forEach((item) => {
        childs.value[item.id] = item
      })
    })
    .catch(() => {
      messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar os sub itens...', timeout: 5000 })
    })
}

function fetchElemento (id) {
  return Resources.Utils.fetch({
    app: 'arq',
    model: 'arqclasse',
    id
  })
    .then((response) => {
      node.value = response.data
      return response
    })
    .catch(() => {
      messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar node...', timeout: 5000 })
    })
}

onMounted(() => {
  reload()
})

defineExpose({
  node_params,
  nodechild_params,
  is_opened,
  node,
  reload
})
</script>

<style lang="scss">
.container-arqtree {
  .node-element {
    position: relative;
    width: 100%;
    color: #444;
    .node-element {
      &:hover {
        color: #000;
      }
    }
    .node-titulo {
      cursor: pointer;
      position: relative;
      display: grid;
      align-items: center;
      border-bottom: 1px solid #aaa0;
      grid-template-areas: "spacer toggle content";
      grid-template-columns: calc(var(--level) * 7px) auto 1fr;
      .content {
        grid-area: content;
        padding: 0 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        line-height: 2;
        a {
          flex-grow: 2;
        }
      }
      .spacer {
        grid-area: spacer;
      }
      .toggle {
        grid-area: toggle;
        display: inline-block;
        padding: 4px 5px;
        color: #777;
        .fa-chevron-down {
          color: #000;
        }
        &:hover {
          color: #00cbad;
          background-color: #0002;
          .fas {
            color: #00cbad;
          }
        }
      }
      .el-actions {
        display: none;
      }
      a {
        text-decoration: none;
      }
      .box-descricao {
        padding: 7px;
        font-size: 90%;
        color: #444;
        position: absolute;
        display: none;
        background-color: #fff;
        left: 60%;
        top: 85%;
        white-space: nowrap;
        border: 1px solid #aaa;
        line-height: 1.3;
      }
      &:hover {
        background-color: #0002;
        border-bottom: 1px solid #aaa;
        .box-descricao {
          display: inline-block;
          z-index: 1;
        }
        .toggle {
          color: #000;
        }
        .el-actions {
          display: inline-block;
        }
      }
    }
    &.type-content {
      .node-titulo {
        padding-left: 10px;
      }
    }
    &.active > .node-titulo {
      background-color: #0001;
      border-bottom: 1px solid #ddd;
    }
  }
}
</style>
