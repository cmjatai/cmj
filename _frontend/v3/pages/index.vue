<template>
  <div>
    ------------------<br />
    <br />
    {{ rserver.__str__ }} <br />
    {{ rserver.ementa }}
    ------------------<br />
    <br />
    {{ rclient.__str__ }} <br />
    {{ rclient.ementa }}

    <div>
      {{ teste }}
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  fetchOnServer: false,
  async asyncData({ params, $axios }) {
    // busca pra construção ssr
    const rserver = await $axios.$get('/materia/materialegislativa/18600/')
    return { rserver }
  },
  data() {
    return {
      rclient: {},
      teste: '',
    }
  },
  mounted() {
    this.teste = 'LEANDRO'
    // busca no cliente
    setTimeout(async () => {
      this.rclient = await this.$axios
        .$get('/materia/materialegislativa/18500/')
        .then((data) => {
          this.sendMessage({
            alert: 'error',
            message: 'erro - Base Atualizada',
            timeout: 30,
          })
          this.sendMessage({
            alert: 'success',
            message: 'success - Base Atualizada',
            timeout: 700,
          })
          this.sendMessage({
            alert: 'info',
            message: data.ementa,
            timeout: 1500,
          })
          return data
        })
    }, 1)
  },
  methods: {
    ...mapActions({
      sendMessage: 'utils/messages/sendMessage',
    }),
  },
}
</script>
