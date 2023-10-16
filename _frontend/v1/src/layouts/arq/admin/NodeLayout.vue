<template>
  <div :class="['node-element', node !== null && node.perfil === 1 ? 'type-content': '']">
    <div :class="['node-titulo', `level-${level}`]" v-if="node">
      <span class="spacer"></span>
      <span class="toggle" v-if="node.perfil !== 1" @click="clickToggle">
        <i v-if="!is_opened || !childs" class="fas fa-chevron-right"></i>
        <i v-if="is_opened && childs" class="fas fa-chevron-down"></i>
      </span>
      <span class="content">
        <router-link :to="{ name: 'childroute', params: { node: node_params, nodechild: node.id } }">{{ node.titulo }}</router-link>
        <div class="btn-group btn-group-sm el-actions">
          <a :href="`/arq/${node.id}`" class="btn btn-link">
            <i class="fas fa-expand"></i>
          </a>
        </div>
        <small v-if="node.descricao" v-html="descricao_html"></small>
      </span>
    </div>
    <node-layout :elemento="raiz" :parent="elemento" :level="level+1" v-for="raiz, k in childs" :key="`class-${k}`" ></node-layout>
  </div>
</template>
<script>
export default {
  name: 'node-layout',
  props: [ 'parent', 'elemento', 'level' ],

  data () {
    return {
      childs: {},
      is_opened: false,
      node_params: this.$route.params.node,
      nodechild_params: this.$route.params.nodechild,
      node: null,
      node_key_localstorage: 'portalcmj_arqnode_tree_opened'
    }
  },
  mounted () {
    this.reload()
  },
  computed: {
    descricao_html: function () {
      let descr = this.node.descricao
      descr = descr.replace('\r\n', '<br>')
      descr = descr.replace('\n', '<br>')
      return `${descr} - ${this.node.id}`
    }
  },
  watch: {
    is_opened: function (nv, ov) {
      if (nv) {
        this.fetch(1, `&get_all=True&parent=${this.node.id}`)
        localStorage.addArrayOfIds(this.node_key_localstorage, this.node.id)
      } else {
        this.$set(this, 'childs', {})
        localStorage.delItemArrayOfIds(this.node_key_localstorage, this.node.id)
      }
    }
  },
  methods: {
    clickToggle () {
      this.is_opened = !this.is_opened
    },
    reload () {
      const _this = this
      _this.node = _this.elemento || null
      if (_this.node_params === 'root' && _this.elemento === undefined) {
        _this.fetch(1, `&get_all=True&parent__isnull=True`)
      } else if (this.elemento === undefined) {
        _this.fetchElemento(_this.node_params)
          .then(() => {
            _this.fetch(1, `&get_all=True&parent=${_this.node_params}`)
              .then(() => {
                _this.clickToggle()
              })
          })
      } else {
        if (localStorage.inArrayOfIds(this.node_key_localstorage, this.node.id)) {
          this.is_opened = true
          this.fetch(1, `&get_all=True&parent=${this.node.id}`)
        }
      }
    },
    fetch (page = 1, query_string = '') {
      const _this = this
      _this.$set(_this, 'childs', {})

      return _this.utils.getModelOrderedList('arq', 'arqclasse', 'titulo', page, query_string)
        .then((response) => {
          _.each(response.data, function (item, idx) {
            _this.$set(_this.childs, item.id, item)
          })
        })
        .catch((response) => _this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar os sub itens...', time: 5 }))
    },
    fetchElemento (id) {
      const _this = this

      return _this.utils.getModel('arq', 'arqclasse', id)
        .then((response) => {
          _this.node = response.data
          return response
        })
        .catch((response) => _this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar node...', time: 5 }))
    }
  }
}
</script>
<style lang="scss" >
.container-arqtree {
  .node-element {
    position: relative;
    width: 100%;
    color: #444;
    .node-element {
      // padding-left: 10px;
      // background-color: #00000007;
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
      small {
        padding: 7px;
        font-style: italic;
        font-size: 110%;
        color: #444;
        position: absolute;
        display: none;
        background-color: white;
        z-index: 1;
        left: 40px;
        top: 100%;
        margin-top: -3px;
        white-space: nowrap;
        border: 1px solid #aaa;
      }
      &:hover {
        background-color: #0001;
        border-bottom: 1px solid #aaa;
        small {
          display: block;
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
  }
}
</style>
