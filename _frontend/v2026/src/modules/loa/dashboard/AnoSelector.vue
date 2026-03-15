<template>
  <div class="ano-selector d-flex gap-2 align-items-center">
    <label
      v-for="loa in items"
      :key="loa.id"
      class="ano-btn"
      :class="{ active: modelValue.includes(loa.ano) }"
    >
      <input
        type="checkbox"
        class="d-none"
        :value="loa.ano"
        :checked="modelValue.includes(loa.ano)"
        @change="toggle(loa.ano)"
      >
      <span class="ano-label">{{ loa.ano }}</span>
    </label>
  </div>
</template>

<script setup>
const props = defineProps({
  items: {
    type: Array,
    required: true
  },
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const toggle = (ano) => {
  const current = [...props.modelValue]
  const idx = current.indexOf(ano)
  if (idx >= 0) {
    if (current.length > 1) current.splice(idx, 1)
  } else {
    current.push(ano)
  }
  emit('update:modelValue', current)
}
</script>

<style lang="scss" scoped>
.ano-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  padding: 0.4rem 1rem;
  border-radius: 2rem;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: 0.02em;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  background: var(--bs-tertiary-bg);
  color: var(--bs-body-color);

  &:hover:not(.active) {
    background: var(--bs-secondary-bg);
    border-color: var(--bs-primary);
    color: var(--bs-primary);
    transform: translateY(-1px);
  }

  &.active {
    background: var(--bs-primary);
    color: #fff;
    border-color: var(--bs-primary);
    box-shadow: 0 2px 8px rgba(var(--bs-primary-rgb), 0.4);
    transform: translateY(-1px);
  }

  .ano-label {
    line-height: 1;
  }
}
</style>
