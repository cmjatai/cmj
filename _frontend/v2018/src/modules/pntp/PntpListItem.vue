<template>
  <div class="pntp-list-item">
    <a :href="'/' + item.slug" class="pntp-list-item__link">
      <div class="pntp-list-item__card card h-100">
        <div class="card-body">
          <div class="body-title d-flex ">
            <span v-if="parent_titulo" class="pntp-list-item__parent text-muted d-block">
              <small>{{ parent_titulo }}</small>
            </span>
            <i :class="['fa', 'fa-lg', item.icon_classe || 'fa-info']"></i>
            <h6 class="pntp-list-item__titulo card-title mb-0">{{ item.titulo }}</h6>
          </div>
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
    },
    parent_titulo: {
      type: String,
      default: null
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-list-item {
  height: 100%;
  .body-title {
    gap: 1rem;
    align-items: center;
    i {
      color: #6c757d77;
    }
  }
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
.pntp-list-item__parent {
  position: absolute;
  top: 0;
  left: 0.2rem;
  line-height: 1;
  small {
    font-variant: small-caps;
    font-size: 0.75rem;
  }
}

.pntp-list-item__card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.pntp-list-item__titulo {
  font-size: 1.2rem;
  font-weight: 700;
  color: #21578d;
  line-height: 1.4;
  transition: color 0.15s ease;
}
</style>
