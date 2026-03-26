<template>
  <div>
    <div
      v-if="items === null"
      class="text-center py-3"
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
      class="text-muted text-center py-3"
    >
      <small>Nenhum registro de prestação de contas encontrado.</small>
      <div v-if="registro && registro.emendaloa">
        <small>Verifique na Emenda Vinculada a Prestação de Contas.</small>
      </div>
    </div>
    <template v-else>
      <div
        v-for="(pc, idx) in items"
        :key="pc.id || idx"
        :class="['pcl-tab-item', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-center px-3 py-1">
          <div>
            <a
              v-if="pc.link_detail_backend"
              :href="pc.link_detail_backend"
              target="_blank"
              rel="noopener"
            >
              <small class="fw-bold">
                {{ pc.prestacao_conta ? (pc.prestacao_conta.__str__ || pc.prestacao_conta.epigrafe || '') : '' }}
              </small>
            </a>
            <br>
            <small class="text-muted">
              <small>Encaminhado em: {{ pc.prestacao_conta ? formatDateBR(pc.prestacao_conta.data_envio) : '—' }}</small>
            </small>
            <small>
              <small v-if="pc.detalhamento"><br>{{ pc.detalhamento }}</small>
              <small
                v-else
                class="text-muted"
              > | Sem descrição de detalhamento</small>

              <template v-if="pc.arquivos && pc.arquivos.length > 0">
                <small class="text-muted">Arquivos:</small>
                <ul class="mb-0">
                  <li
                    v-for="(arquivo, aidx) in pc.arquivos"
                    :key="arquivo.id || aidx"
                  >
                    <a
                      :href="arquivo.arquivo"
                      target="_blank"
                      rel="noopener"
                    >
                      {{ arquivo.descricao || arquivo.__str__ || 'Arquivo sem descrição' }}
                    </a>
                  </li>
                </ul>
              </template>
              <template v-else>
                <small class="text-muted"> | Nenhum arquivo anexado.</small>
              </template>
            </small>
            <template v-if="pc.registro_ajuste && registro && pc.registro_ajuste.id !== registro.id">
              <hr class="p-0 m-0">
              <small class="text-muted">Relativo ao Ajuste Técnico: {{ pc.registro_ajuste.descricao || pc.registro_ajuste.__str__ }}</small>
            </template>
          </div>
          <span :class="['badge', `text-bg-${situacaoVariant(pc.situacao)}`]">
            {{ situacaoLabel(pc.situacao) }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { situacaoVariant, situacaoLabel, formatDateBR } from '../utils/pcl-helpers'

defineProps({
  items: { type: Array, default: null },
  registro: { type: Object, default: null }
})
</script>
