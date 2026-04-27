<template>
  <div class="pntp-list-item">
    <a :href="'/' + item.slug" class="pntp-list-item__link">
      <div class="pntp-list-item__card card h-100">
        <div class="card-body">
          <h6 class="pntp-list-item__titulo card-title mb-0">{{ item.titulo }}</h6>
        </div>
      </div>
    </a>
  </div>
</template>

<script>
export default {
  name: 'pntp-list-item',
  props: {
    item: {
      type: Object,
      required: true
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-list-item {
  height: 100%;
}

.pntp-list-item__link {
  display: block;
  height: 100%;
  text-decoration: none;
  color: inherit;

  &:hover .pntp-list-item__card {
    border-color: var(--primary, #007bff);
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
  }

  &:hover .pntp-list-item__titulo {
    color: var(--primary, #007bff);
  }
}

.pntp-list-item__card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.pntp-list-item__titulo {
  font-size: 0.9rem;
  font-weight: 500;
  color: #343a40;
  line-height: 1.4;
  transition: color 0.15s ease;
}
</style>
