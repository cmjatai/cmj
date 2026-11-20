<template>
  <div
    v-if="totais"
    class="totalizadores d-flex flex-wrap gap-2"
  >
    <div class="totalizador-card totalizador-total">
      <div class="totalizador-icon">
        <FontAwesomeIcon icon="coins" />
      </div>
      <div class="totalizador-info">
        <span class="totalizador-valor">{{ formatCurrency(totais.disp_total) }}</span>
        <span class="totalizador-label">Disponibilidade Global</span>
      </div>
    </div>

    <div class="totalizador-card totalizador-saude">
      <div class="totalizador-icon">
        <FontAwesomeIcon icon="heart-pulse" />
      </div>
      <div class="totalizador-info">
        <span class="totalizador-valor">{{ formatCurrency(totais.disp_saude) }}</span>
        <span class="totalizador-label">Saúde</span>
      </div>
    </div>

    <div class="totalizador-card totalizador-diversos">
      <div class="totalizador-icon">
        <FontAwesomeIcon icon="layer-group" />
      </div>
      <div class="totalizador-info">
        <span class="totalizador-valor">{{ formatCurrency(totais.disp_diversos) }}</span>
        <span class="totalizador-label">Áreas Diversas</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  totais: {
    type: Object,
    default: null
  }
})

const formatCurrency = (value) => {
  if (value == null) return 'R$ 0,00'
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  })
}
</script>

<style lang="scss" scoped>
.totalizador-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1 1 0;
  padding: 0.5rem;
  //border-radius: 0.75rem;
  // background: rgba(var(--bs-body-bg-rgb), 0.5);
  //border: 1px solid var(--bs-border-color);
  transition: all 0.25s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: rgba(var(--bs-body-bg-rgb), 0.8);
  }

  [data-bs-theme="dark"] & {
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
  }
}

.totalizador-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.625rem;
  font-size: 1.15rem;
  flex-shrink: 0;
}

.totalizador-total .totalizador-icon {
  background: rgba(var(--bs-primary-rgb), 0.12);
  color: var(--bs-primary);
}

.totalizador-saude .totalizador-icon {
  background: rgba(var(--bs-success-rgb), 0.12);
  color: var(--bs-success);
}

.totalizador-diversos .totalizador-icon {
  background: rgba(var(--bs-warning-rgb), 0.12);
  color: var(--bs-warning);
}

.totalizador-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.totalizador-label {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--bs-secondary-color);
  white-space: nowrap;
}

.totalizador-valor {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--bs-body-color);
  white-space: nowrap;
}
</style>
