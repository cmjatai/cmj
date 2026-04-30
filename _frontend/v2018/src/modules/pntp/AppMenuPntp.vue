<template>
  <nav v-if="root" class="pntp-menu">
    <div v-if="parent_slug" class="pntp-menu__back">
      <a :href="'/' + parent_slug" class="pntp-menu__back-link">
        <i class="fa fa-chevron-left"></i>
        <span v-if="parent_title">
          {{ parent_title }}
        </span>
      </a>
    </div>
    <h5 class="pntp-menu__titulo">
      <span
        :class="['pntp-menu__titulo-link', { 'active': isRootSelected }]"
        @click="$emit('select', root.id)"
      >{{ root.titulo }}</span>
    </h5>
    <ul v-if="rootChildsRenderable.length" class="pntp-menu__list list-unstyled mt-2 mb-0">
      <pntp-menu-item
        v-for="childId in rootChildsRenderable"
        :key="childId"
        :item="items[childId]"
        :items="items"
        :selected_id="selected_id"
        @select="$emit('select', $event)"
      ></pntp-menu-item>
    </ul>
  </nav>
</template>

<script>
export default {
  name: 'app-menu-pntp',
  props: {
    items: {
      type: Object,
      required: true
    },
    selected_id: {
      type: [Number, String],
      default: null
    },
    parent_slug: {
      type: String,
      default: null
    },
    parent_title: {
      type: String,
      default: null
    }
  },
  computed: {
    root () {
      return Object.values(this.items).find(item => item.parent === null) || null
    },
    rootChildsRenderable () {
      if (!this.root || !this.root.childs) return []
      return this.root.childs.filter(id => {
        const child = this.items[id]
        return child && (
          (child.childs && child.childs.length > 0) ||
          (child.documentos && child.documentos.length > 0)
        )
      })
    },
    isRootSelected () {
      return this.root && String(this.selected_id) === String(this.root.id)
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-menu {
  // background: #fff;
  // border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 0.3rem;
}

.pntp-menu__titulo {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.2rem;
  padding-bottom: 0.2rem;
  margin-top: 1rem;
  border-bottom: 1px solid var(--primary, #007bff);
}

.pntp-menu__titulo-link {
  color: #343a40;
  text-decoration: none;
  cursor: pointer;

  &.active {
    color: var(--primary, #007bff);
  }

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }
}

.pntp-menu__back {
  // border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  margin-top: -0.5rem;
  margin-left: -0.3rem;
  margin-bottom: 0.3rem;
  font-variant: small-caps;
}

.pntp-menu__back-link {
  font-size: 0.8rem;
  color: #6c757d;
  text-decoration: none;

  &:hover {
    color: var(--primary, #007bff);
    text-decoration: none;
  }

  i {
    font-size: 0.7rem;
  }
}
.pntp-menu__list {
  margin: 0;
  padding: 0;
}
</style>
