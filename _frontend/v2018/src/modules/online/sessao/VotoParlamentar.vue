<template>
  <div :class="['voto-parlamentar']">
    <a href="#" class="btn btn-lg btn-success">SIM</a>
    <a href="#" class="btn btn-lg btn-danger">NÃO</a>
    <a href="#" class="btn btn-lg btn-warning">Abstenção</a>
  </div>
</template>
<script>
export default {
  name: 'voto-parlamentar',
  props: ['item'],
  components: {
  },
  data () {
    return {
      app: [],
      model: []
    }
  },
  watch: {
  },
  computed: {
  },
  mounted () {
    this.refresh()
  },
  methods: {
    refresh () {
    }
  }
}
</script>

<style lang="scss">
.voto-parlamentar {
  position: absolute;
  top: 0em;
  right: 0em;
  left: 0;
  bottom: 0;
  display: flex;
  gap: 2em;
  background-color: #0008;
  justify-content: center;
  align-items: center;
  zoom: 2;
  .btn {
    padding: 1em;
    line-height: 0;
    box-shadow: 0.5em 0.5em 1em #000;
    font-family: 'Graduate', 'Courier New', Courier, monospace;
    font-weight: bold;
    &:hover {
      box-shadow: 0.5em 0.5em 1em #222;
    }
  }
}

@media screen and (max-width: 991.98px) {
  .voto-parlamentar {
    zoom: 1.7;
  }
}
@media screen and (max-width: 800px) {
  .voto-parlamentar {
    zoom: 1.5;
  }
}
@media screen and (max-width: 600px) {
  .voto-parlamentar {
    zoom: 1;
  }
}
@media screen and (max-width: 480px) {
  .voto-parlamentar {
    zoom: 1;
    gap: 1em;
    .btn {
      padding: 1em 0.7em;
    }
  }
}
</style>
