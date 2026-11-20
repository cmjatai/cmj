<template>
  <div class="container-fluid container-arqtree">
    <div class="row">
      <div id="col-classes">
        <div class="arqtree-inner">
          <div class="arqtree-titulo">
            <span
              class="collapse-all"
              @click="clickCollapseAll"
            >
              <FontAwesomeIcon icon="chevron-left" />
              <FontAwesomeIcon icon="chevron-left" />
            </span>
            <h1>ArqView</h1>
          </div>
          <NodeLayout
            :level="0"
            ref="noderootRef"
          />
        </div>
      </div>
      <div id="col-docs">
        <router-view
          :key="route.fullPath"
          ref="selectednodeRef"
          @check-is-opened-nodes-tree="checkIsOpenedNodesTree"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import NodeLayout from './NodeLayout.vue'
import Split from 'split.js'
import { clearArrayOfIds, delItemArrayOfIds } from '~@/utils/storageArray'

const route = useRoute()
const router = useRouter()
const messageStore = useMessageStore()

const noderootRef = ref(null)
const selectednodeRef = ref(null)
const node_key_localstorage = 'portalcmj_arqnode_tree_opened'
const check_opened = ref(0)

watch(route, (nv, old) => {
  if (nv.name === 'arqchildroute' && nv.params.node !== old.params.node) {
    if (noderootRef.value) {
      noderootRef.value.node_params = nv.params.node
      noderootRef.value.nodechild_params = nv.params.nodechild
      noderootRef.value.reload()
    }
  }
})

function checkIsOpenedNodesTree () {
  check_opened.value += 1
}

function clickCollapseAll () {
  if (noderootRef.value?.is_opened) {
    clearArrayOfIds(node_key_localstorage)
    noderootRef.value.is_opened = false
  } else {
    const node = noderootRef.value?.node
    let node_parent = ''
    if (node !== null && node?.parent !== null) {
      node_parent = node.parent
    } else {
      node_parent = 'root'
    }

    const selectednode = selectednodeRef.value
    if (selectednode && selectednode.classe && selectednode.classe.parent != null) {
      const name = 'arqchildroute'
      const params = {
        node: node_parent,
        nodechild: selectednode.classe.parent
      }
      delItemArrayOfIds(node_key_localstorage, selectednode.classe.parent)
      router.push({ name, params })
    } else if ((node && node.id !== node_parent) || route.params.nodechild !== undefined) {
      let name = 'arqadminroute'
      const params = { node: node_parent }
      if (node_parent !== 'root') {
        params.nodechild = node_parent
        name = 'arqchildroute'
      }
      router.push({ name, params })
    } else {
      clearArrayOfIds(node_key_localstorage)
      noderootRef.value?.reload()
      messageStore.addMessage({ type: 'danger', text: 'Topo atingido!', timeout: 2000 })
    }
  }
}

onMounted(() => {
  let sizes = localStorage.getItem('split-sizes')
  if (sizes) {
    sizes = JSON.parse(sizes)
    if (sizes[0] + sizes[1] > 100) {
      sizes = [35, 65]
    }
  } else {
    sizes = [35, 65]
  }
  Split(['#col-classes', '#col-docs'], {
    minSize: 350,
    sizes,
    onDragEnd: (sizes) => {
      localStorage.setItem('split-sizes', JSON.stringify(sizes))
    }
  })
})
</script>

<style lang="scss">
@use "sass:list";
.container-arqtree {
  padding: 15px;
  & > .row {
    min-height: 70vh;
    position: relative;
  }
  #col-docs {
    z-index: 0;
    flex: 1 1 auto;
  }
  #col-classes {
    z-index: 1;
  }
  .arqtree-inner {
    position: sticky;
    display: block;
    top: 0;
  }
  .gutter {
    background-color: #eee;
    background-repeat: no-repeat;
    background-position: 53% 30%;
  }
  .gutter.gutter-horizontal {
    background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAeCAYAAADkftS9AAAAIklEQVQoU2M4c+bMfxAGAgYYmwGrIIiDjrELjpo5aiZeMwF+yNnOs5KSvgAAAABJRU5ErkJggg==');
    cursor: col-resize;
    padding: 0;
  }
  .arqtree-titulo {
    display: flex;
    align-items: center;
    .collapse-all {
      margin-left: -10px;
      cursor: pointer;
      padding: 10px 12px 10px 10px;
      display: inline-block;
      line-height: 1;
      &:hover {
        color: red;
      }
    }
    h1 {
      margin: 0;
      padding: 0;
      line-height: 1;
      display: inline-block;
    }
  }

  $levels: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9;
  @each $l in $levels {
    .level-#{$l} {
      --level: #{$l};
    }
  }
}
</style>
