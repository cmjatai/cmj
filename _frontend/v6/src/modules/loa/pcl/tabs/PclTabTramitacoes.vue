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
      Nenhuma tramitação encontrada para a matéria vinculada.
    </div>
    <template v-else>
      <div
        v-for="(tram, idx) in items"
        :key="tram.id || idx"
        :class="['p-3', 'pcl-tab-item', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-start flex-wrap">
          <div class="me-2">
            <small class="fw-bold">{{ formatDateBR(tram.data_tramitacao) }}</small>
            <span
              v-if="tram.turno"
              class="badge text-bg-light ms-1"
            >
              <small>Turno: {{ tram.turno.__str__ || tram.turno }}</small>
            </span>
            <span
              v-if="tram.urgente"
              class="badge text-bg-danger ms-1"
            >
              <small>Urgente</small>
            </span>
          </div>
          <span class="badge text-bg-info">
            {{ tram.status ? (tram.status.__str__ || tram.status) : '—' }}
          </span>
        </div>
        <div class="mt-1">
          <small class="text-muted">
            {{ tram.unidade_tramitacao_local ? (tram.unidade_tramitacao_local.__str__ || tram.unidade_tramitacao_local) : '' }}
            <template v-if="tram.unidade_tramitacao_destino">
              &rarr; {{ tram.unidade_tramitacao_destino.__str__ || tram.unidade_tramitacao_destino }}
            </template>
          </small>
        </div>
        <div
          class="mt-1"
          v-if="tram.texto"
        >
          <small class="text-muted">{{ truncate(tram.texto, 40) }}</small>
        </div>
        <small
          class="text-muted d-block"
          v-if="tram.data_encaminhamento"
        >
          Encaminhamento: {{ formatDateBR(tram.data_encaminhamento) }}
        </small>
        <small
          class="text-muted d-block"
          v-if="tram.data_fim_prazo"
        >
          Fim do prazo: {{ formatDateBR(tram.data_fim_prazo) }}
        </small>
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
  const t = text.__str__ || text
  const words = t.split(/\s+/)
  if (words.length <= wordCount) return t
  return words.slice(0, wordCount).join(' ') + ' …'
}
</script>
