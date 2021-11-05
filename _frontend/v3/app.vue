<template>
  <div>
    {{m1.ementa}}<br>
    ---------------
    {{m2.ementa}}<br>
    ---------------
    {{message}}
  </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  async setup() {
    const [{ data: m1 }, { data: m2 }] = await Promise.all([
      useFetch(`https://www.jatai.go.leg.br/api/materia/materialegislativa/18856/`),
      useFetch(`https://www.jatai.go.leg.br/api/materia/materialegislativa/18855/`)
    ])

    return {
      m1,
      m2
    }
  },
  data () {
    return {
      message: Array()
    }
  },
  mounted () {
    const t = this
    t.$options.sockets.onmessage = function (event: MessageEvent) {
      const data = JSON.parse(event.data)
      t.message.push(data)
      console.log(event)
    }
  }
})
</script>
