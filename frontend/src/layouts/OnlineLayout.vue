<template>
  <base-layout>

    <template slot="brand">
      <brand></brand>
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

    <template slot="header-right">
      <i class="fas fa-sign-out-alt hover-circle" @click="close" title="Sair da Interface Sapl Online"></i>
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
  data () {
    return {
    }
  },
  methods: {
    close () {
      window.location.href = '/'
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
