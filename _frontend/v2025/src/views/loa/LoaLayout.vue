<template>
  <div>
    <router-view v-slot="{ Component }">
      <component :is="Component">
        <slot></slot>
      </component>
    </router-view>
  </div>
</template>

<script>
export default {
  name: 'LoaLayout',
  methods: {
  },
  mounted: function () {
    // this.removeAside()
  }
}
</script>
