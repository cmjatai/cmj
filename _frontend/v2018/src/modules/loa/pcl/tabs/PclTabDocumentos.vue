<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted small py-3 text-center">
      Nenhum documento acessório encontrado para a matéria vinculada.
    </div>
    <template v-else>
      <div
        v-for="(doc, idx) in items"
        :key="doc.id || idx"
        :class="['hover', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-start p-3">
          <div>
            <a
              v-if="doc.arquivo"
              :href="doc.arquivo"
              class="btn btn-primary btn-sm mr-2"
              target="_blank"
              rel="noopener"
            >
              <i class="fas fa-file-pdf fa-sm"></i>
            </a>
            <small class="font-weight-bold">{{ doc.nome ? (doc.nome.__str__ || doc.nome) : '—' }}</small>
            <br>
            <small class="text-muted">
              {{ doc.tipo ? (doc.tipo.__str__ || doc.tipo) : '' }}
              &mdash;
              {{ formatDateBR(doc.data) }}
            </small>
            <template v-if="doc.autor">
              <br><small class="text-muted">Autor: {{ doc.autor }}</small>
            </template>
            <template v-if="doc.ementa">
              <br><small class="text-muted">{{ truncate(doc.ementa, 30) }}</small>
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { formatDateBR } from '../utils/pcl-helpers'

export default {
  name: 'pcl-tab-documentos',
  props: {
    items: {
      type: Array,
      default: null
    }
  },
  methods: {
    formatDateBR,
    truncate (text, wordCount) {
      if (!text) return ''
      const words = text.split(/\s+/)
      if (words.length <= wordCount) return text
      return words.slice(0, wordCount).join(' ') + ' …'
    }
  }
}
</script>
