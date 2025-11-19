<template>
  <div class="side-right">
    <div class="menu">
      <ul>
        <li>
          <img
            @click="toogleNormaDestaque"
            src="/imgs/icon_normas_juridicas_destaque.png"
          >
          <ul>
            <li
              v-for="item in normasDeDestaque"
              :key="`srmd${item.id}`"
            >
              <button
                type="button"
                class="btn btn-secondary"
                data-toggle="modal"
                data-target="#modal-norma"
                @click="modalOpened=item"
              >
                {{ item.apelido }}
              </button>
            </li>
          </ul>
        </li>
      </ul>
    </div>
    <Teleport
      v-if="modalOpened"
      :to="`#modalCmj`"
    >
      <NormaSimpleModalView
        :html-id="`modal-opened-${modalOpened.id}`"
        :norma-id="modalOpened.id"
        @close="modalOpened = null"
      />
    </Teleport>
  </div>
</template>

<script setup>
import NormaSimpleModalView from '~@/components/NormaSimpleModalView.vue'
import { ref, onMounted, computed } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
const syncStore = useSyncStore()
const modalOpened = ref(null)

onMounted(() => {
  syncStore.fetchSync({
    app: 'norma',
    model: 'normajuridica',
    action: 'destaques',
    params: {
      get_all: true
    }
  })
})

const menuNormaDestaque = ref(false)
const toogleNormaDestaque = () => {
  menuNormaDestaque.value = !menuNormaDestaque.value
}

const normasDeDestaque = computed(() => {
  return Object.values(syncStore.data_cache?.norma_normajuridica || {}).filter(
    norma => norma.norma_de_destaque === true
  ).sort((a, b) => {
    if (a.apelido < b.apelido) return -1
    if (a.apelido > b.apelido) return 1
    return 0
  })
})

</script>
<style lang="scss" scoped>
.side-right {
  position: absolute;
  top: 3em;
  bottom: 0;
  width: 100%;
  text-align: center;
  background-color: var(--cmj-background-color);
  border-left: 1px solid var(--bs-border-color-translucent);
  // box-shadow: -10px 0 20px var(--bs-body-bg);

  .menu {
    ul {
      list-style-type: none;
      padding: 0;
      margin: 0;
      li {
        margin-bottom: 1em;
        img {
          cursor: pointer;
          width: 2.5em;
        }
        ul {
          position: absolute;
          top: 0;
          right: 100%;
          height: calc(100vh - 3em);
          z-index: 1;
          white-space: nowrap;
          display: none;
          flex-direction: column;
          justify-content: stretch;
          li {
            flex: 1 1 auto;
            margin: 0;
            padding: 0;
            button {
              height: 100%;
              width: 100%;
              text-align: left;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              border-radius: 0;
            }
            &:not(:last-child) {
              border-bottom: 1px solid var(--bs-border-color);
            }
          }
        }
        &:hover ul {
          display: flex;
        }
      }
    }
  }
}
</style>
