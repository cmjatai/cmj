<template>
  <div
    v-if="pagination.total_entries"
    class="widget-pagination d-flex justify-content-between align-items-center"
  >
    <span
      :class="['arrow', pagination.previous_page != null ? 'hover-circle' : 'disabled']"
      @click="previousPage"
    >
      <i class="fas fa-chevron-left" />
    </span>
    <div class="pages">
      {{ pagination.start_index }}–{{ pagination.end_index }} de {{ pagination.total_entries }}
      <div class="inner">
        <BPagination
          align="end"
          :total-rows="pagination.total_entries"
          v-model="currentPageModel"
          :per-page="pageSize"
        />
      </div>
    </div>
    <span
      :class="['arrow', pagination.next_page != null ? 'hover-circle' : 'disabled']"
      @click="nextPage"
    >
      <i class="fas fa-chevron-right" />
    </span>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  pagination: {
    type: Object,
    default: () => ({})
  },
  pageSize: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['nextPage', 'previousPage', 'currentPage'])

const currentPageModel = ref(props.pagination.page || 1)

watch(
  () => props.pagination,
  (nv) => {
    if (nv?.page) {
      currentPageModel.value = nv.page
    }
  },
  { deep: true }
)

watch(currentPageModel, (nv, ov) => {
  if (nv !== ov) {
    emit('currentPage', nv)
  }
})

function nextPage () {
  if (props.pagination.next_page != null) {
    emit('nextPage')
  }
}

function previousPage () {
  if (props.pagination.previous_page != null) {
    emit('previousPage')
  }
}
</script>
<style lang="scss">
.widget-pagination {
  position: relative;
  border: 1px #dddddd solid;
  border-radius: 20px;
  cursor: pointer;
  &:hover {
  }
  .arrow {
    display: grid;
    align-items: center;
    justify-items: center;
    height: 38px;
    width: 38px;
    cursor: pointer;
  }
  .disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
  .pages {
    line-height: 38px;
    position: static;
    user-select: none;
    .inner {
      z-index: 2;
      position: absolute;
      top: 100%;
      margin-top: -3px;
      right: 50%;
      transform: translateX(50%);
      display: none;
      padding: 15px 15px 0;
      border: 1px #dddddd solid;
      background-color: var(--bs-body-bg);
      border-color: var(--bs-border-color-translucent);
    }
    &:hover {
      .inner {
        display: inline-block;
      }
    }
  }
}
</style>
