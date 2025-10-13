<template>
  <nav aria-label="breadcrumb" v-if="parents">
    <ol class="breadcrumb">
      <li class="breadcrumb-item" v-for="parent, k in parents_and_me" :key="`cp-${k}`">
        <router-link :to="{ name: 'arqchildroute', params: { node: k > 0 ? parents[k-1].id : 'root', nodechild: parent.id } }"
          @click.native="clickItemBreadCrumb">
          {{ parent.titulo }}
        </router-link>
      </li>
    </ol>
  </nav>
</template>
<script>

export default {
  name: 'bread-crumb-classe',
  props: [ 'parents', 'me' ],
  data () {
    return {
      parents_and_me: []
    }
  },
  mounted () {
    const t = this
    t.$nextTick()
      .then(function () {
        if (t.me === undefined) {
          t.parents_and_me = t.parents
          return
        }
        t.parents_and_me = t.parents.concat([{
          id: t.me.id,
          titulo: t.me.titulo
        }])
      })
  },
  computed: {
  },
  methods: {
    clickItemBreadCrumb () {
      this.$refs.noderoot.reload()
    }
  }
}
</script>
<style lang="scss">
</style>
