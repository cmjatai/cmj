<template>
  <div
    :id="htmlId"
    class="modal norma-simple-modal-view fade show"
    tabindex="-1"
  >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5
            class="modal-title"
            v-html="norma ? (norma.apelido !== '' ? `${norma.apelido}<br>` : '') + norma.__str__ : 'Carregando...' "
          />
          <button
            type="button"
            class="btn-close"
            @click="emit('close')"
          />
        </div>
        <div
          v-if="normaRender"
          class="modal-body"
          v-html="normaRender"
        />
        <div v-else class="modal-body">
          Carregando texto...
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            @click="emit('close')"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { ref, onMounted, computed, nextTick } from 'vue'
import axios from 'axios'

const emit = defineEmits(['close'])

const syncStore = useSyncStore()

const props = defineProps({
  htmlId: {
    type: String,
    required: true
  },
  normaId: {
    type: [Number, null],
    required: false,
    default: null
  }
})

const normaRender = ref(null)

const norma = computed(() => {
  return syncStore.data_cache?.norma_normajuridica?.[props.normaId] || null
})

onMounted(() => {
  syncStore.fetchSync({
    app: 'norma',
    model: 'normajuridica',
    id: props.normaId,
    params: {},
    force_fetch: false
  }).then(() => {

    axios.get(
      `/norma/${props.normaId}/ta?embedded`
    ).then((res) => {
      normaRender.value = res.data
      nextTick(() => {
        const links = document.querySelectorAll(
          '.cp a:not([target="_blank"])'
        )
        links.forEach((link) => {
          link.setAttribute('target', '_blank')
          link.setAttribute('rel', 'noopener noreferrer')
        })
      })
    })

  })
})

</script>

<style lang="scss">

@import '~@/scss/compilacao.scss';

.norma-simple-modal-view {
  background-color: #000b;
  z-index: 10000;
  display: block;

  .cp {
    line-height: 1.5em;

    .cp-linha-vigencias,
    .vigencia-active,
    .dptt .dne,
    .btns-action,
    .btn-group,
    .tipo-vigencias {
      display: none !important;
    }

    a {
      text-decoration: none !important;
      //cursor: default;
    }
  }
}

@media screen and (max-width: 480px) {}
</style>
