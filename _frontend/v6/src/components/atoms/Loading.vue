<template>
  <div class="loading" :style="{ position: position }">
    <div class="loader" />
    <div
      class="message"
      v-if="message"
    >
      {{ message }}
    </div>
  </div>
</template>
<script setup>

const props = defineProps({
  message: {
    type: String,
    default: ''
  },
  position: {
    type: String,
    default: 'fixed' // or 'absolute'
  }
})

</script>

<style lang="scss" scoped>

.loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fffa;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2em;
  .message {
    font-size: 3em;
  }
  .loader {
    width: 50px;
    aspect-ratio: 1;
    display: grid;
    border: 4px solid #0000;
    border-radius: 50%;
    border-color: #ccc #0000;
    animation: l16 1s infinite linear;
    zoom: 2;
  }
  .loader::before,
  .loader::after {
    content: "";
    grid-area: 1/1;
    margin: 2px;
    border: inherit;
    border-radius: 50%;
  }
  .loader::before {
    border-color: #f03355 #0000;
    animation: inherit;
    animation-duration: .8s;
    animation-direction: reverse;
  }
  .loader::after {
    margin: 8px;
  }
  @keyframes l16 {
    100%{transform: rotate(1turn)}
  }
}

</style>
