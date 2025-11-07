<template>
  <root-layout>
    <template #header-left>
      <button
        class="d-lg-none"
        type="button"
        data-bs-toggle="offcanvas"
        data-bs-target="#menuSideLeft"
        aria-controls="menuSideLeft"
      >☰</button>
    </template>

    <template #brand>
      <brand></brand>
    </template>

    <template #header-detail>
    </template>

    <template #header-right>
    </template>

    <template #sideleft>
      <side-left></side-left>
    </template>

    <template #sideright>
      <side-right></side-right>
    </template>

    <template #main>
      <router-view></router-view>
    </template>
  </root-layout>
</template>

<script setup>
import RootLayout from './RootLayout.vue'
import SideLeft from './SideLeft.vue'
import Brand from './Brand.vue'
// 1. Imports

// 2. Composables

// 3. Props & Emits

// 4. State & Refs

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks

// 8. Functions
</script>
<style lang="scss">
</style>
