<template>
  <div class="w-100 inner inner-sideright">
    <ul>
      <li>
        <b-img @click="toogleNormaDestaque" src="@/assets/img/icon_normas_juridicas_destaque.png" fluid rounded="0" />
        <ul :class="['list-group', 'isr-hover', menu_norma_destaque ? 'show': '']">
          <li class="list-group-item"><a href="#">Teste 1</a></li>
          <li class="list-group-item"><a href="#">Teste 2</a></li>
          <li class="list-group-item"><a href="#">Teste 3</a></li>
          <li class="list-group-item"><a href="#">Teste 4</a></li>
        </ul>
      </li>
    </ul>

    <!--b-img src="@/assets/img/icon_mesa_diretora.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_comissoes.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_parlamentares.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_pautas.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_plenarias.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_materia_legislativa.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_normas_juridicas.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_relatorios.png" fluid rounded="0" /-->
  </div>
</template>

<script>
export default {
  name: 'side-right',
  data () {
    return {
      mainProps: { class: 'icon' },
      menu_norma_destaque: false
    }
  },
  methods: {
    toogleNormaDestaque (event) {
      this.menu_norma_destaque = !this.menu_norma_destaque
    }
  }
}
</script>

<style lang="scss">
.inner-sideright {
  //display: none;
  & > ul {
    padding: 0;
    margin: 0;
    list-style-type: none;
    & >li {
      position: relative;
    }
  }
  ul {
    &.isr-hover {
      position: absolute;
      right: 90%;
      top: 50%;
      display: none;
      &.show {
        display: flex;
      }
      a {
        white-space: nowrap;
      }
    }
  }
  img {
    padding: 15px;
    cursor: pointer;
    &:hover {
      background-color:  #ddd;
    }
  }
}
</style>
