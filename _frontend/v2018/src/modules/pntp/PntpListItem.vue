<template>
  <div class="pntp-list-item">
    <div v-if="permissionEdit" class="pntp-list-item__actions">
      <a target="_blank" :href="`/classe/${item.id}/edit`" class="btn btn-sm btn-outline-link" title="Abrir em nova aba">
        <i class="fa fa-edit"></i>
      </a>
      <!-- botão para copiar o href de pntp-list-item__link para área de transferência -->
      <button
        class="btn btn-sm btn-outline-link"
        title="Copiar link"
        @click.stop="copyToClipboard(href)"
      >
        <i class="fa fa-link"></i>
      </button>
    </div>
    <a :href="href" class="pntp-list-item__link">
      <div class="pntp-list-item__card card h-100">
        <div class="card-atricon">{{ item.atricon }}</div>
        <div class="card-body">
          <div class="body-title d-flex ">
            <div class="body-title__parts d-flex">
              <span v-if="parent_titulo" class="pntp-list-item__parent text-muted d-block">
                <small>{{ parent_titulo }}</small>
              </span>
              <span class="icon-item">
                <i :class="['fa-xl', item.icon_classe || 'fa fa-lg fa-info']"></i>
              </span>
              <h6 class="pntp-list-item__titulo card-title mb-0">{{ item.titulo }}</h6>
              <i class="fa fa-chevron-right"></i>
            </div>
          </div>
          <small v-if="item.subtitle" class="pntp-list-item__subtitle text-muted mb-0 mt-1" v-html="item.subtitle"></small>
          <div v-if="item.descricao" class="pntp-list-item__descricao mt-2" v-html="renderedDescricao"></div>
        </div>
      </div>
    </a>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, typographer: true })

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
    },
    root_slug: {
      type: String,
      default: ''
    }
  },
  computed: {
    permissionEdit () {
      return this.permissions.includes('sigad.change_classe')
    },
    href () {
      /* if (this.root_slug && this.item.slug && this.item.slug.includes(this.root_slug)) {
        return '/' + this.root_slug + '?categoria=' + this.item.id
      } */
      return '/' + this.item.slug
    },
    renderedDescricao () {
      if (!this.item.descricao) return ''
      return md.render(this.item.descricao)
    }
  },
  methods: {
    copyToClipboard (text) {
      console.log(text)
      this.sendMessage({ alert: 'info', message: 'Copiado para a área de transferência!', time: 5 })
      // montar o link completo usando o hostname atual + href
      const fullLink = window.location.origin + this.href
      navigator.clipboard.writeText(fullLink).catch(err => {
        console.error('Erro ao copiar para área de transferência: ', err)
        this.sendMessage({ alert: 'danger', message: 'Erro ao copiar para área de transferência', time: 5 })
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.pntp-list-item {
  height: 100%;
  .body-title {
    gap: 0.5rem;
    align-items: center;
    justify-content: space-between;
    i {
      color: #6c757d99;
    }
  }
  .body-title__parts {
    gap: 0.5rem;
    align-items: center;
    i {
      color: #6c757d55;
    }
    i.fa-chevron-right {
      margin-left: auto;
      color: #6c757d00;
    }
  }
  .icon-item {
    display: flex;
    width: 2.5rem;
    height: 2.5rem;
    margin-left: -0.66rem;
    justify-content: center;
    align-items: center;
    background: #f0f0f0 url(~@/assets/img/bg.png);
    border-radius: 4px;
    &:hover {
      background-color: var(--primary, #007bff);
      i {
        color: #fff;
      }
    }
  }
}

.pntp-list-item__link {
  display: block;
  height: 100%;
  text-decoration: none;
  color: inherit;
  .card-atricon {
    position: absolute;
    top: 0.2rem;
    right: 0.5rem;
    font-size: 1.5rem;
    color: #6c757d22;
  }

  &:hover {
    .pntp-list-item__card {
      border-color: var(--primary, #007bff);
      box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
    }
    .pntp-list-item__titulo {
      color: var(--primary, #007bff);
    }
    i {
      color: var(--primary, #007bff);
    }
    i.fa-chevron-right {
      margin-top: 3px;
      color: var(--primary, #007bff55);
    }
    .card-atricon {
      color: var(--primary, #007bff44);
    }

  }

}

.pntp-list-item__parent {
  position: absolute;
  top: 0;
  left: 0.35rem;
  line-height: 1;
  small {
    font-variant: small-caps;
    font-size: 0.85rem;
  }
}

.pntp-list-item__card {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  .card-body {
    padding-bottom: 0.5rem;
  }
}

.pntp-list-item__titulo {
  font-size: 1.2rem;
  font-weight: 700;
  color: #21578d;
  line-height: 1;
  transition: color 0.15s ease;
}
.pntp-list-item__subtitle {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 1.2;
  font-style: italic;
}
.pntp-list-item__descricao {
  font-size: 0.95rem;
  color: #343a40;
  line-height: 1.4;
  font-style: italic;
}
.pntp-list-item__actions {
  position: absolute;
  bottom: 0.25rem;
  right: 1.1rem;
  display: flex;
  gap: 0.25rem;
  z-index: 1;
  a, button {
    text-decoration: none;
    color: #929aa1;
    &:hover {
      color: var(--primary, #007bff);
    }
  }
}
</style>
