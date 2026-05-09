<template>
  <div class="pntp-doclist-item">
    <a :href="href" class="pntp-doclist-item__link">
      <div class="pntp-doclist-item__card card h-100">
        <div class="card-body">
          <div class="body-title d-flex">
            <span v-if="parent_titulo" class="pntp-doclist-item__parent text-muted d-block">
              <small>{{ parent_titulo }}</small>
            </span>
            <span class="icon-item">
              <i :class="['fa-xl', doc.icon_doc || 'fa-solid fa-file-text']"></i>
            </span>
            <div class="pntp-doclist-item__content">
              <h6 class="pntp-doclist-item__titulo card-title mb-0">{{ doc.titulo }}</h6>
              <p v-if="doc.descricao" class="pntp-doclist-item__descricao text-muted mb-0 mt-1">{{ doc.descricao }}</p>
            </div>
          </div>
          <div v-if="doc.texto" class="pntp-doclist-item__texto mt-2" v-html="renderedTexto"></div>
        </div>
      </div>
    </a>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

export default {
  name: 'pntp-doclist-item',
  props: {
    doc: {
      type: Object,
      required: true
    },
    parent_titulo: {
      type: String,
      default: null
    },
    root_slug: {
      type: String,
      default: ''
    }
  },
  computed: {
    href () {
      return '/' + this.doc.slug
      /* if (this.root_slug && this.doc.slug && this.doc.slug.includes(this.root_slug)) {
        return '/' + this.root_slug + '?categoria=' + (this.doc._parent_id || this.doc.id)
      } */
    },
    renderedTexto () {
      if (!this.doc.texto) return ''
      return md.render(this.doc.texto)
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-doclist-item {
  height: 100%;
  .body-title {
    gap: 1rem;
    align-items: flex-start;
    i {
      color: #6c757d77;
    }
  }
  .icon-item {
    display: flex;
    min-width: 2rem;
    min-height: 2.5rem;
    justify-content: center;
    align-items: center;
    flex-shrink: 0;
  }
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
  &:hover i {
    color: var(--primary, #007bff);
  }
}

.pntp-doclist-item__parent {
  position: absolute;
  top: 0;
  left: 0.35rem;
  line-height: 1;
  small {
    font-variant: small-caps;
    font-size: 0.75rem;
  }
}

.pntp-doclist-item__card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  .card-body {
    padding-bottom: 0.5rem;
  }
}

.pntp-doclist-item__titulo {
  font-size: 1.2rem;
  font-weight: 700;
  color: #21578d;
  line-height: 1;
  transition: color 0.15s ease;
}

.pntp-doclist-item__content {
  flex: 1;
  min-width: 0;
}

.pntp-doclist-item__descricao {
  font-size: 0.85rem;
  color: #6c757d;
  line-height: 1.4;
}

.pntp-doclist-item__texto {
  font-size: 0.85rem;
  color: #495057;
  line-height: 1.5;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 0.5rem;

  :deep(p) { margin-bottom: 0.4rem; }
  :deep(p:last-child) { margin-bottom: 0; }
  :deep(ul), :deep(ol) { padding-left: 1.2rem; margin-bottom: 0.4rem; }
  :deep(a) { color: var(--primary, #007bff); }
}
</style>
