<template>
  <div v-if="pagination.total_entries !== 0" class="widget-pagination d-flex justify-content-between align-items-center">
    <span :class="['arrow', pagination.previous_page !== null ? 'hover-circle' : 'disabled']" @click="previousPage">
      <i class="fas fa-chevron-left"></i>
    </span>
    <div class="pages">
      {{pagination.start_index}}–{{pagination.end_index}} de {{pagination.total_entries}}
      <div class="inner">
        <b-pagination align="right" :total-rows="pagination.total_entries" v-model="currentPage" :per-page="18"/>
      </div>
    </div>
    <span :class="['arrow', pagination.next_page !== null ? 'hover-circle' : 'disabled']"  @click="nextPage">
      <i class="fas fa-chevron-right"></i>
    </span>
  </div>
</template>
<script>
export default {
  name: 'pagination',
  props: ['pagination'],
  data () {
    return {
      currentPage: this.pagination.page
    }
  },
  watch: {
    currentPage: function (nv, ov) {
      if (nv !== ov) {
        this.$emit('currentPage', nv)
      }
    },
    pagination: function (nv) {
      this.currentPage = nv.page
    }
  },
  methods: {
    nextPage () {
      if (this.pagination.next_page !== null) this.$emit('nextPage')
    },
    previousPage () {
      if (this.pagination.previous_page !== null) this.$emit('previousPage')
    }
  }
}
</script>
<style lang="scss">
.widget-pagination {

  position: relative;
  background-color: rgba(white, 0.2);
  border: 1px #dddddd solid;
  border-radius: 20px;
  cursor: pointer;
  &:hover {
    background-color: rgba(white, 0.7);
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
      z-index: 1;
      position: absolute;
      top: 100%;
      right: 20px;
      display: none;
      padding: 15px 15px 0;
      border: 1px #dddddd solid;
      background-color: rgba($color: white, $alpha: 0.9);
    }
    &:hover {
      .inner {
        display: inline-block;
      }
    }
  }
}
</style>
