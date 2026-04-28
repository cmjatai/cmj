<template>
  <div class="pntp-doclist-item">
    <a :href="'/' + doc.slug" class="pntp-doclist-item__link">
      <div class="pntp-doclist-item__card card h-100">
        <div class="card-body">
          <h6 class="pntp-doclist-item__titulo card-title mb-0">{{ doc.titulo }}</h6>
        </div>
      </div>
    </a>
  </div>
</template>

<script>
export default {
  name: 'pntp-doclist-item',
  props: {
    doc: {
      type: Object,
      required: true
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-doclist-item {
  height: 100%;
}

.pntp-doclist-item__link {
  display: block;
  height: 100%;
  text-decoration: none;
  color: inherit;

  &:hover .pntp-doclist-item__card {
    border-color: var(--primary, #007bff);
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
  }

  &:hover .pntp-doclist-item__titulo {
    color: var(--primary, #007bff);
  }
}

.pntp-doclist-item__card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.pntp-doclist-item__titulo {
  font-size: 0.9rem;
  font-weight: 500;
  color: #343a40;
  line-height: 1.4;
  transition: color 0.15s ease;
}
</style>
