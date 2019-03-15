<template>
  <div class="w-100 inner inner-sideright">
    <b-img src="@/assets/img/icon_mesa_diretora.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_comissoes.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_parlamentares.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_pautas.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_plenarias.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_materia_legislativa.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_normas_juridicas.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_normas_juridicas_destaque.png" fluid rounded="0" />
    <b-img src="@/assets/img/icon_relatorios.png" fluid rounded="0" />
  </div>
</template>

<script>
export default {
  name: 'side-right',
  data () {
    return {
      mainProps: { class: 'icon' }
    }
  }
}
</script>

<style lang="scss">
.inner-sideright {
  display: none;
  img {
    padding: 15px;
    cursor: pointer;
    &:hover {
      background-color:  #ddd;
    }
  }
}
</style>
