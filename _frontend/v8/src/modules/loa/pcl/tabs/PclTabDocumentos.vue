<template>
  <div>
    <div
      v-if="items === null"
      class="text-center py-2"
    >
      <div
        class="spinner-border spinner-border-sm"
        role="status"
      >
        <span class="visually-hidden">Carregando...</span>
      </div>
      Carregando...
    </div>
    <div
      v-else-if="items.length === 0"
      class="text-muted small py-3 text-center"
    >
      Nenhum documento acessório encontrado para a matéria vinculada.
    </div>
    <template v-else>
      <div
        v-for="(doc, idx) in items"
        :key="doc.id || idx"
        :class="['pcl-tab-item', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-start p-3">
          <div>
            <a
              v-if="doc.arquivo"
              :href="doc.arquivo"
              class="btn btn-primary btn-sm me-2"
              target="_blank"
              rel="noopener"
            >
              <FontAwesomeIcon
                icon="file-pdf"
                size="sm"
              />
            </a>
            <small class="fw-bold">{{ doc.nome ? (doc.nome.__str__ || doc.nome) : '—' }}</small>
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

<script setup>
import { formatDateBR } from '../utils/pcl-helpers'

defineProps({
  items: { type: Array, default: null }
})

function truncate (text, wordCount) {
  if (!text) return ''
  const words = text.split(/\s+/)
  if (words.length <= wordCount) return text
  return words.slice(0, wordCount).join(' ') + ' …'
}
</script>
