<template>
  <div class="w-100 h-100 d-flex flex-column align-items-start inner inner-sideleft">
    <router-link :to="{ name: item.route }" v-for="(item, key) in links" :key="key" @click.native="selectRoute(item)" :class="isSelected(item)">
      <span class="hover-circle icon">
        <b-img :src="item.image" fluid rounded="0" />
      </span>
      <span class="text-link">
        {{item.texto}}
      </span>

    </router-link>

  </div>
</template>

<script>
export default {
  name: 'side-right',
  data () {
    return {
      selected: '',
      links: [
        {
          image: require('@/assets/img/icon_mesa_diretora.png'),
          route: 'index_link',
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
        }
      ]
    }
  },
  computed: {
  },
  methods: {
    isSelected (item) {
      return item.texto === this.selected ? 'selected' : ''
    },
    selectRoute (item) {
      this.selected = item.texto
    }
  }
}
</script>

<style lang="scss">
.inner-sideleft {
  padding-top: 8px;
  //background: linear-gradient(to right, rgba(9, 20, 38, 0.95) 0%, #000000 100%);
  a {
    text-decoration: none;
    cursor: pointer;
    height: 40px;
    width: 100%;
    display: grid;
    grid-template-columns: 64px minmax(0px,186px);
    align-items: center;
    .icon {
      text-align: center;
      margin: 0 12px 0;
      padding: 6px 0;
    }
    img {
      height: 28px;
    }
    .text-link {
      color: #555;
      white-space: nowrap;
      display: none;
      position: absolute;
      left: 100%;
      margin-left: -5px;
    }
    &:hover, &.selected .icon {
      text-decoration: none;
      position: relative;
      background-color: #dddddd;
      .text-link {
        background-color: #dddddd;
        display: block;
        border-radius: 0 24px 24px 0;
        padding: 8px 24px 8px 0;
      }
    }
    &.selected .icon  {
      border-radius: 50%;
    }
  }
}

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

</style>
