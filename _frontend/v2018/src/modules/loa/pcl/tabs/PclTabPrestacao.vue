<template>
  <div>
    <div v-if="items === null" class="text-center py-3">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted text-center py-3">
      <small>Nenhum registro de prestação de contas encontrado.</small>
      <div v-if="registro && registro.emendaloa">
        <small>Verifique na Emenda Vinculada a Prestação de Contas.</small>
      </div>
    </div>
    <template v-else>
      <div
        v-for="(pc, idx) in items"
        :key="pc.id || idx"
        :class="['hover', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-center px-3 py-1">
          <div>
            <a
              v-if="pc.link_detail_backend"
              :href="pc.link_detail_backend"
              target="_blank"
              rel="noopener"
            >
              <small class="font-weight-bold">
                {{ pc.prestacao_conta ? (pc.prestacao_conta.__str__ || pc.prestacao_conta.epigrafe || '') : '' }}
              </small>
            </a>
            <br>
            <strong>
              <small>Encaminhado em: {{ pc.prestacao_conta ? formatDateBR(pc.prestacao_conta.data_envio) : '—' }}</small>
            </strong>
            <template v-if="pc.detalhamento">
              <br><small class="text-muted">{{ pc.detalhamento }}</small>
            </template>
            <template v-if="pc.registro_ajuste">
              <hr class="p-0 m-0">
              <small class="text-muted">Relativo ao Ajuste Técnico: {{ pc.registro_ajuste.descricao || pc.registro_ajuste.__str__ }}</small>
            </template>
          </div>
          <b-badge :variant="situacaoVariant(pc.situacao)">
            {{ situacaoLabel(pc.situacao) }}
          </b-badge>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { situacaoVariant, situacaoLabel, formatDateBR } from '../utils/pcl-helpers'

export default {
  name: 'pcl-tab-prestacao',
  props: {
    items: {
      type: Array,
      default: null
    },
    registro: {
      type: Object,
      default: null
    }
  },
  methods: {
    situacaoVariant,
    situacaoLabel,
    formatDateBR
  }
}
</script>
