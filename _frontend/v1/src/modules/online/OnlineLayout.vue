<template>
  <base-layout>

    <template slot="brand">
      <brand></brand>
    </template>
    <template slot="header-detail">
        <div class="btn-group ml-2 btn-group-sm accessibility" role="group" aria-label="First group">
          <a class="btn btn-outline-dark" @click="diminuirFonte">a</a>
          <a class="btn btn-outline-dark" @click="aumentarFonte">A</a>
        </div>
    </template>
    <template slot="header-right">
      <i class="fas fa-sign-out-alt hover-circle" @click="close" title="Sair da Interface Online"></i>
    </template>

    <template slot="sideleft">
      <side-left></side-left>
    </template>

    <template slot="sideright">
      <side-right></side-right>
    </template>

    <template slot="main">
      <router-view></router-view>
    </template>

  </base-layout>
</template>

<script>
import SideRight from './fragments/SideRight'
import SideLeft from './fragments/SideLeft'
import Brand from './fragments/Brand'
import BaseLayout from './fragments/BaseLayout'

export default {
  name: 'online',
  components: {
    BaseLayout,
    SideRight,
    SideLeft,
    Brand
  },
  beforeDestroy: function () {
    this.$disconnect()
  },
  methods: {
    close () {
      window.location.href = '/'
    },
    diminuirFonte () {
      $('.base-layout .main').css('font-size', '-=1')
    },
    aumentarFonte () {
      $('.base-layout .main').css('font-size', '+=1')
    }
  }
}
</script>

<style lang="scss">
.header-right {
  display: grid;
  align-items: center;
  justify-items: center;
  i {
    color: rgba(black, 0.5);
    padding: 8px;
    cursor: pointer;
    &:hover {
      color: black;
    }
  }
}
</style>
