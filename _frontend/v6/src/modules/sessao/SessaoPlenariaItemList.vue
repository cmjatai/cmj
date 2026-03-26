<template>
  <router-link
    :class="'sessao-plenaria-item-list'"
    :to="{ name: 'sessao_plenaria_view_link', params: {id: sessao.id} }"
  >
    <h4 class="tit">
      {{ titulo }}
    </h4>
    <div class="subtitulo">
      <span>{{ subtitulo }}</span><span class="separator"> – </span>
      <span>{{ date_text }}</span>
    </div>
  </router-link>
</template>
<script setup>
import { computed } from 'vue'

const props = defineProps({
  sessao: {
    type: Object,
    required: true
  }
})

const month_text = (month) => {
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]
  return monthNames[month] || ''
}

const titulo = computed(() => {
  let sessao = props.sessao
  let tipo = sessao.tipo
  let data_inicio = new Date(sessao.data_inicio)

  let base = `${sessao.numero}ª ${tipo.nome}`

  // acesso direto ao objeto tipo que foram
  // baixados via resource e não está ligado ao syncStore
  if (tipo.tipo_numeracao === 1) { base += ` da ${data_inicio.getDate() > 15 ? 2 : 1}ª Quinzena do mês de ${month_text(data_inicio.getMonth())}` }

  if (tipo.tipo_numeracao === 2) { base += ` do mês de ${month_text(data_inicio.getMonth())}` }

  if (tipo.tipo_numeracao <= 10) { base += ` de ${data_inicio.getFullYear()}` }

  return base
})

const subtitulo = computed(() => {
  let sessao = props.sessao
  // acesso direto ao objeto legislatura e sessao_legislativa que foram
  // baixados via resource e não está ligado ao syncStore
  return `${sessao.sessao_legislativa.numero}ª Sessão Legislativa da
              ${sessao.legislatura.numero}ª Legislatura`
})

const date_text = computed(() => {
  let sessao = props.sessao
  let data_inicio = new Date(`${sessao.data_inicio}T${sessao.hora_inicio}`)
  return `${data_inicio.getDate()} de
              ${month_text(data_inicio.getMonth())} de
              ${data_inicio.getFullYear()} – ${sessao.hora_inicio}`
})

</script>
<style lang="scss">
.sessao-plenaria-item-list {
  display: grid;
  grid-template-columns: auto auto;
  align-items: center;
  border-bottom: 1px solid var(--bs-border-color-translucent);
  padding: 1em;
  line-height: 1;
  grid-column-gap: 0.5em;
  cursor: pointer;

  &:first-child {
    border-top: 1px solid var(--bs-border-color-translucent);
  }

  &:hover {
    background-color: var(--nav-bg-hover-color);
    text-decoration: none;
  }
  .subtitulo {
    color: var(--bs-secondary-text-color);
    display: inline-block;
    text-align: right;
    line-height: 1.2;
    .separator {
      display: block;
      height: 0px;
      overflow: hidden;
    }
  }
  h3 {
    line-height: 1;
    color: var(--bs-highlight-color);
    margin-bottom: 0px;
  }
}

[data-bs-theme="dark"] {
  .sessao-plenaria-item-list {
    color: var(--bs-link-color);
  }
}

@media screen and (max-width: 1199px) {
  .sessao-plenaria-item-list {
    grid-template-columns: auto;
    line-height: 1.3;
    h3 {
      font-size: 110%;
    }
    .subtitulo {
      line-height: 1;
      text-align: left;
    }
  }
}
@media screen and (max-width: 600px) {
  .sessao-plenaria-item-list {
    h3 {
      font-size: 100%;
    }
    .subtitulo {
    }
  }
}
@media screen and (max-width: 480px) {
  .sessao-plenaria-item-list {
    padding: 0.5em;
    h3 {
      font-size: 85%;
    }
    .subtitulo {
      font-size: 75%;
    }
  }
}
</style>
