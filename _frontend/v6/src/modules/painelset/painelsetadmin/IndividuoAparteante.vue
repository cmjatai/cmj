<template>
  <div class="individuo-aparteante-component">
    <div
      :class="['individuo-aparteante', ]"
      v-if="individuo"
      :key="`individuo-aparteante-${individuo.id}`"
      :ref="`individuo-aparteante-${individuo.id}`"
    >
      <div class="inner-individuo">
        <div class="individuo-header">
          <div class="name">
            <strong>EM APARTE:</strong>
            {{ individuo ? individuo.name : 'Carregando indivíduo...' }}
          </div>
        </div>
      </div>
      <div class="inner-individuo">
        <div class="individuo">
          <div class="avatar">
            <img
              v-if="fotografiaUrl"
              :src="fotografiaUrl"
              alt="Foto do parlamentar"
            >
            <FontAwesomeIcon
              v-else
              icon="user-circle"
              size="2x"
            />
          </div>
        </div>
        <div class="divide" />
        <div class="cronometro">
          <cronometro-palavra
            :key="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :ref="`cronometro-com-a-palavra-${individuo.cronometro}`"
            :cronometro_id="individuo.cronometro"
            :controls="[
              // 'toggleDisplay',
              'pause',
              'resume',
              'add30s',
              'add1m'
            ]"
          />
          <div
            class="icon-status-microfone"
            @click="toggleMicrofone"
          >
            <FontAwesomeIcon
              v-if="individuo && individuo.status_microfone"
              icon="microphone"
            />
            <FontAwesomeIcon
              v-else
              icon="microphone-slash"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed, inject } from 'vue'
import { useSyncStore } from '~@/stores/SyncStore'
import CronometroPalavra from './CronometroPalavra.vue'

const syncStore = useSyncStore()
const EventBus = inject('EventBus')

const props = defineProps({
  individuo_id: {
    type: Number,
    required: false,
    default: null
  }
})

const individuo = computed(() => {
  if (props.individuo_id && syncStore.data_cache?.painelset_individuo) {
    return syncStore.data_cache.painelset_individuo[props.individuo_id] || null
  }
  return null
})

const fotografiaUrl = computed(() => {
  if (individuo.value?.fotografia) {
    return '/api/painelset/individuo/' + individuo.value.id + '/fotografia.c96.png'
  } else if (individuo.value?.parlamentar) {
    return '/api/parlamentares/parlamentar/' + individuo.value.parlamentar + '/fotografia.c96.png'
  }
  return ''
})

const toggleMicrofone = () => {
  EventBus.emit('toggle-microfone-individuo', individuo.value.id)
}
</script>
<style lang="scss">
.individuo-aparteante-component {
  .individuo-aparteante {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    margin-left: 5em;
    .inner-individuo {
      display: flex;
      flex-direction: row;
      align-items: stretch;
      justify-content: flex-start;
      width: auto;
    }
    .individuo-header {
      text-align: left;
      font-size: 1.2em;
      color: #bb0;
      width: 100%;
      .name {
        background-color: #444;
        white-space: nowrap;
        margin: 0;
        padding: 7px 14px 6px;
        text-align: left;
        display: inline-block;
      }
    }
    .individuo {
      flex: 1 1 auto;
    }
    .divide {
      width: 1px;
      background-color: #888;
      margin: 0;
    }
    .cronometro {
      flex: 1 1 auto;
      padding: 1em;
      font-size: 0.9em;
      position: relative;
      .icon-status-microfone {
        position: absolute;
        top: 0em;
        right: 0.5em;
        cursor: pointer;
        font-size: 4em;
        color: #ccc;
        i {
          &.fa-microphone {
            color: #4c4;
          }
          &.fa-microphone-slash {
            color: #c44;
          }
        }
      }
    }
    .croncard {
      justify-content: center;
      gap: 1em;
    }
    .controls {
      &.visible {
        .btn-group {
          margin: 0;
          width: auto;
          .btn {
            padding: 0.5em 1.5em 0.6em 1.5em;
          }
        }
      }
    }
    .individuo {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 2em 1em;
      .avatar {
        opacity: 1 !important;
        width: 5em;
        height: 5em;
        img {
          box-shadow: 0px 0px 30px #444;
        }
        i {
          color: #ccc;
          font-size: 4em;
        }
      }
    }
  }
}
@media screen and (max-width: 1399.98px) {
  .individuo-aparteante-component {
    .individuo-aparteante {
      margin-left: 4em;
      .cronometro {
        padding: 0.5em;
        font-size: 0.8em;
        .icon-status-microfone {
          right: 0.5em;
          font-size: 4em;
        }
      }
      .croncard {
        justify-content: center;
        gap: 1em;
      }
      .controls {
        &.visible {
          .btn-group {
            .btn {
              padding: 0.4em 1em 0.4em 1em;
            }
          }
        }
      }
    }
  }
}
@media screen and (max-width: 1199.98px) {

.individuo-aparteante-component {
  .individuo-aparteante {
    margin-left: 2em;
    .cronometro {
      font-size: 0.9em;
      .icon-status-microfone {
        font-size: 3.5em;
      }
    }
    .croncard {
      justify-content: center;
      gap: 1em;
    }
    .controls {
      &.visible {
        .btn-group {
          margin: 0;
          width: auto;
          .btn {
            font-size: 1.7em;
            padding: 0.6em;
          }
        }
      }
    }
  }
}
}
@media screen and (max-width: 991.98px) {
  .individuo-aparteante-component {
    .individuo-aparteante {
      border-top: 1px solid #888;
      margin-top: 0em;
      align-items: flex-end;
      margin-left: 0;
      .individuo-header {
        .name {
          display: flex;
          flex-direction: column;
          text-align: right;
          font-size: 1em;
          padding: 5px 10px 4px;
          margin: 0.5em 0.5em 0 0.5em;
          strong {
            display: inline-block;
            width: 100%;
          }
        }
      }
      .inner-individuo {
        flex-direction: column;
          min-width: 70%;
      }
      .cronometro {
        padding: 0.5em;
        .icon-status-microfone {
          font-size: 2em;
          top: 0.3em;
          right: 0.5em;
        }
      }
      .individuo {
        padding: 0.5em;
        .avatar {
          i {
            font-size: 3em;
          }
        }
      }
    }
  }
}
</style>
