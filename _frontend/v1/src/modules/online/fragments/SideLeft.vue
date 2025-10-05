<template>
  <div class="w-100 d-flex flex-column align-items-start inner inner-sideleft">
    <router-link :to="{ name: item.route }" v-for="(item, key) in links_filter" :key="key+1" @click.native="selectRoute(item)" :class="[isSelected(item), isClicked(item)]" @mouseover.native="mouseover(item)" @mouseleave.native="mouseleave(item)">
      <span class="hover-circle icon">
        <i v-if="item.icon" :class="item.icon"></i>
        <b-img v-else :src="item.image" fluid rounded="0" />
      </span>
      <span class="text-link">
        {{item.texto}}
      </span>
    </router-link>

  </div>
</template>

<script>
export default {
  name: 'side-left',
  data () {
    return {
      selected: '',
      clicked: '',
      links: [
        {
          image: require('@/assets/img/icon_mesa_diretora.png'),
          route: '',
          texto: 'Mesa Diretora'
        },
        {
          image: require('@/assets/img/icon_comissoes.png'),
          route: '',
          texto: 'Comissões'
        },
        {
          image: require('@/assets/img/icon_parlamentares.png'),
          route: '',
          texto: 'Parlamentares'
        },
        {
          image: require('@/assets/img/icon_pautas.png'),
          route: '',
          texto: 'Pautas'
        },
        {
          image: require('@/assets/img/icon_plenarias.png'),
          route: 'sessao_list_link',
          texto: 'Sessões Plenárias'
        },
        {
          image: require('@/assets/img/icon_materia_legislativa.png'),
          route: '',
          texto: 'Matérias Legislativas'
        },
        {
          image: require('@/assets/img/icon_normas_juridicas.png'),
          route: '',
          texto: 'Normas Jurídicas'
        },
        {
          image: require('@/assets/img/icon_relatorios.png'),
          route: '',
          texto: 'Relatórios'
        },
        {
          icon: 'fas fa-columns',
          route: 'painelset_list_link',
          texto: 'Painéis',
          permission: 'painelset.list_evento',
          hasPermission: false
        }
      ]
    }
  },
  computed: {
    links_filter: function () {
      return this.links.filter(i => i.route !== '' && (i.permission === undefined || (i.hasPermission !== undefined && i.hasPermission)))
    }
  },
  methods: {
    isSelected (item) {
      return item.route === this.selected ? 'selected' : ''
    },
    isClicked (item) {
      return item.texto === this.clicked ? 'clicked' : ''
    },
    mouseover (item) {
      let t = this
      t.clicked = item.texto
    },
    mouseleave (item) {
      let t = this
      t.clicked = ''
    },
    selectRoute (item) {
      let t = this
      t.selected = item.route
      t.clicked = item.texto
      setTimeout(() => {
        t.clicked = ''
      }, 500)
    },
    user_logged_in () {
      let t = this
      t.selected = ''
      t.links.forEach((item, key) => {
        if (item.permission !== undefined) {
          t.hasPermission(item.permission)
            .then((response) => {
              t.links[key].hasPermission = true
            })
            .catch(() => {
              t.links[key].hasPermission = false
            })
        }
      })
    },
    user_logged_out () {
      let t = this
      t.selected = ''
      t.links.forEach((item, key) => {
        if (item.permission !== undefined) {
          t.links[key].hasPermission = false
        }
      })
    }
  },
  mounted () {
    this.selected = this.$route.name
    this.user_logged_in()
  }
}
</script>

<style lang="scss">

@import "~@/scss/variables";

.inner-sideleft {
  padding-top: 8px;
  // background: linear-gradient(to right, rgba(9, 20, 38, 0.95) 0%, #000000 100%);

  a {
    text-decoration: none;
    cursor: pointer;
    height: $width-sideleft * 0.6;
    width: 100%;
    display: grid;
    grid-template-columns: $width-sideleft minmax(0px, $width-sideleft * 3);
    align-items: center;
    .icon {
      text-align: center;
      margin: 0 12px 0;
      padding: 6px 0;
    }
    img {
      height: $width-sideleft * 0.4;
    }
    .text-link {
      color: #555;
      white-space: nowrap;
      display: none;
      position: absolute;
      left: 100%;
      margin-left: -5px;
      line-height: $width-sideleft * 0.6;
      z-index: 1;
    }
    &.clicked{
      text-decoration: none;
      position: relative;
      background-color: #dddddd;
      .text-link {
        background-color: #dddddd;
        display: block;
        border-radius: 0 24px 24px 0;
        padding: 0px 12px 0px 0;
      }
    }
    &.selected .icon  {
      border-radius: 50%;
      width: $width-sideleft * 0.6;
      height: $width-sideleft * 0.6;
      background-color: #dddddd;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

@media screen and (max-width: 800px) {
  $width-sideleft: 48px;
  .inner-sideleft {
    a {
      grid-template-columns: 48px 0px;
      .icon {
        margin: 0 5px;
      }
    }
  }
}

@media screen and (max-width: 480px) {
  $width-sideleft: 40px;
  .inner-sideleft {
    a {
      grid-template-columns: 40px 0px;
      .icon {
        margin: 0 2px;
      }
    }
  }
}

@media screen and (min-width: 481px) {

  .base-layout.left-expand {
    .sideleft {
      background-color: rgba($color: #f5f5f5, $alpha: 1);
      padding-right: 8px;
    }
    .inner-sideleft {
      .text-link {
        display: inline-block;
        position: relative;
        left: auto;
      }
      a:hover, a.selected  {
        background-color: #dddddd;
        border-radius: 0 24px 24px 0;
      }
    }
  }

}

</style>
