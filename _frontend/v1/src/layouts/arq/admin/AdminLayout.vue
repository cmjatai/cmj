<template>
  <div class="container-fluid container-arqtree">
    <div class="row">
      <div id="col-classes">
        <div class="arqtree-inner">
          <div class="arqtree-titulo">
            <span class="collapse-all" @click="clickCollapseAll">
              <i class="fas fa-chevron-left"></i>
              <i class="fas fa-chevron-left"></i>
            </span>
            <h1>ArqAdmin</h1>
          </div>
          <node-layout :level="0" ref="noderoot"></node-layout>
        </div>
      </div>
      <div id="col-docs">
        <router-view :key="$route.fullPath"></router-view>
      </div>
    </div>
  </div>
</template>
<script>
import NodeLayout from './NodeLayout.vue'
import Split from 'split.js'
export default {
  name: 'admin-layout',
  components: { NodeLayout },
  watch: {
    $route: function (nv, old) {
      this.$refs.noderoot.node_params = this.$route.params.node
      this.$refs.noderoot.nodechild_params = this.$route.params.nodechild
      this.$refs.noderoot.reload()
    }
  },
  methods: {
    clickCollapseAll () {
      if (this.$refs.noderoot.is_opened) {
        localStorage.clearArrayOfIds('portalcmj_arqnode_tree_opened')
        this.$refs.noderoot.reload()
      } else {
        const node = this.$refs.noderoot.node
        let node_parent = ''

        if (node !== null && node.parent !== null) {
          node_parent = node.parent
        } else {
          node_parent = 'root'
        }
        if ((!_.isEmpty(node) && node.id !== node_parent) || this.$route.params.nodechild !== undefined) {
          this.$router.push({
            name: 'adminroute',
            params: {
              node: node_parent
            }
          })
        } else {
          this.sendMessage(
            { alert: 'danger', message: 'Topo atingido!', time: 2 })
        }
      }
    }
  },
  mounted () {
    let sizes = localStorage.getItem('split-sizes')
    if (sizes) {
      sizes = JSON.parse(sizes)
    } else {
      sizes = [50, 50]
    }
    Split(['#col-classes', '#col-docs'], {
      minSize: 350,
      sizes: sizes,
      onDragEnd: function (sizes) {
        localStorage.setItem('split-sizes', JSON.stringify(sizes))
      }
    })
  }
}
</script>
<style lang="scss" >
@use "sass:list";
.container-arqtree {
  padding: 15px;
  & > .row {
    min-height: 70vh;
    position: relative;
  }
  .arqtree-inner {
    position: sticky;
    display: block;
    top: 0;
  }
  .gutter {
    background-color: #ddd;
    background-repeat: no-repeat;
    background-position: 50%;
  }
  .gutter.gutter-horizontal {
      background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAeCAYAAADkftS9AAAAIklEQVQoU2M4c+bMfxAGAgYYmwGrIIiDjrELjpo5aiZeMwF+yNnOs5KSvgAAAABJRU5ErkJggg==');
      cursor: col-resize;
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
