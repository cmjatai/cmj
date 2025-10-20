<template>
  <div :class="
    ['node-element',
    node !== null && node.count_childs === 0 ? 'type-content': '',
    node !== null && node.id === parseInt(nodechild_params) ? 'active': ''
    ]">
    <div :class="['node-titulo', `level-${level}`]" v-if="node">
      <span class="spacer"></span>
      <span class="toggle" v-if="node.count_childs !== 0" @click="clickToggle">
        <i v-if="!is_opened || !childs" class="fas fa-chevron-right"></i>
        <i v-if="is_opened && childs" class="fas fa-chevron-down"></i>
      </span>
      <span class="content">
        <router-link :to="{ name: 'arqchildroute', params: { node: node_params, nodechild: node.id } }"
          @click.native="clickRoute">
          {{ node.titulo }}
          <i v-if="node.checkcheck" class="fas fa-xs fa-lock text-light-blue" title="ArqClasse Arquivada."></i>
        </router-link>
        <div class="btn-group btn-group-sm el-actions">
          <a :href="`/arqadmin/classe/${node.id}`" target="_blank" class="btn btn-link">
            <i class="fas fa-edit"></i>
          </a>
          <a :href="`/arq/${node.id}/${node.id}`" class="btn btn-link">
            <i class="fas fa-expand"></i>
          </a>
        </div>
        <small class="box-descricao" v-html="descricao_html"></small>
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
      node_key_localstorage: 'portalcmj_arqnode_tree_opened',
      click_title: false,
      ARQCLASSE_FISICA: 100,
      ARQCLASSE_LOGICA: 200
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
      return `<strong>${this.node.conta}</strong> - <strong>${this.node.titulo}</strong><br><i>${descr}</i>`
    }
  },
  watch: {
    is_opened: function (nv, ov) {
      if (nv) {
        this.fetch(1, `&get_all=True&parent=${this.node.id}`)
        localStorage.addArrayOfIds(this.node_key_localstorage, this.node.id)
      } else {
        this.$set(this, 'childs', {})
        if (!_.isEmpty(this.node)) {
          localStorage.delItemArrayOfIds(this.node_key_localstorage, this.node.id)
        }
      }
    },
    $route: function (nv, old) {
      const t = this
      t.node_params = nv.params.node
      t.nodechild_params = nv.params.nodechild
      // console.debug(nv)
      t.$nextTick()
        .then(function () {
          t.openIfInArrayOfIds()
        })
    }
  },
  methods: {
    clickRoute () {
      this.clickToggle()
      /* if (this.click_title) {

      } else {
        this.click_title = true
      } */
    },
    clickToggle () {
      this.is_opened = !this.is_opened
    },
    openIfInArrayOfIds () {
      if (!_.isEmpty(this.node) && !this.is_opened && localStorage.inArrayOfIds(this.node_key_localstorage, this.node.id)) {
        this.is_opened = true
        this.fetch(1, `&get_all=True&parent=${this.node.id}`)
      }
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
        _this.openIfInArrayOfIds()
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
