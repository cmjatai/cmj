<template>
  <div
    class="alert alert-info fade show alert-dismissible"
    role="alert"
  >
    <slot />
    <button
      type="button"
      class="btn-close"
      data-bs-dismiss="alert"
      aria-label="Close"
    />
  </div>
</template>
<script>
  export default {
    name: 'Alert'
  }
</script>
<script setup>

</script>
