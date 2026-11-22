<template>
  <div class="flex flex-col gap-2">
    <div
      class="v8-barra-acoes"
      role="group"
      aria-label="Modals"
    >
      <button
        type="button"
        class="v8-btn"
        data-ds-acao="confirmar"
        @click="confirmar('padrao')"
      >
        Confirmação
      </button>
      <button
        type="button"
        class="v8-btn v8-btn-perigo"
        data-ds-acao="confirmar-perigo"
        @click="confirmar('perigo')"
      >
        Confirmação de perigo
      </button>
      <button
        type="button"
        class="v8-btn"
        data-ds-acao="modal"
        @click="abrirModal"
      >
        Modal
      </button>
      <button
        type="button"
        class="v8-btn"
        data-ds-acao="formulario"
        @click="abrirFormulario"
      >
        Formulário
      </button>
      <button
        type="button"
        class="v8-btn"
        data-ds-acao="assistente"
        @click="abrirAssistente"
      >
        Assistente
      </button>
      <button
        type="button"
        class="v8-btn"
        data-ds-acao="tela-cheia"
        @click="abrirTelaCheia"
      >
        Tela cheia
      </button>
    </div>
    <div
      class="v8-barra-acoes"
      role="group"
      aria-label="Toasts"
    >
      <button
        v-for="item in NIVEIS_DE_TOAST"
        :key="item.nivel"
        type="button"
        class="v8-btn"
        :data-ds-toast="item.nivel"
        @click="toast[item.nivel](item.texto)"
      >
        {{ item.rotulo }}
      </button>
    </div>
    <p
      class="text-sm text-texto-suave"
      aria-live="polite"
      data-ds-resultado
    >
      {{ resultado }}
    </p>
  </div>
</template>

<script setup>
// Ilha `ds-overlays` da vitrine (V8-DS-009): abre cada tipo de modal e de toast com conteúdo de
// amostra. Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { ref } from 'vue'
import { useModal } from '~@/overlays/useModal'
import { useToast } from '~@/overlays/useToast'
import { NIVEIS_DE_TOAST, enviarAmostra, passosDoAssistente } from '~@/modules/ds/amostras'

// 2. Composables
const { confirm, openModal, openForm, openWizard, openFullscreen } = useModal()
const toast = useToast()

// 4. State & Refs
const resultado = ref('')

// 8. Functions
const conteudo = () => import('~@/modules/ds/modais/AmostraConteudo.vue')

async function confirmar(variante) {
  const ok = await confirm({
    titulo: 'Confirmação',
    mensagem: 'Seguir com a ação de exemplo?',
    rotuloOk: variante === 'perigo' ? 'Excluir' : 'Seguir',
    variante
  })
  resultado.value = ok ? 'Confirmado.' : 'Cancelado.'
}

async function abrirModal() {
  await openModal(conteudo, {}, { title: 'Modal' })
  resultado.value = 'Modal fechado.'
}

async function abrirFormulario() {
  const dados = await openForm(() => import('~@/modules/ds/modais/AmostraForm.vue'), {}, { title: 'Formulário' })
  resultado.value = dados ? `Salvo: ${dados.nome}.` : 'Formulário descartado.'
}

async function abrirAssistente() {
  const dados = await openWizard({
    title: 'Assistente',
    passos: passosDoAssistente,
    dados: { nome: '', email: '', bairro: '' },
    concluir: enviarAmostra
  })
  resultado.value = dados ? `Concluído: ${dados.nome}, ${dados.bairro}.` : 'Assistente descartado.'
}

async function abrirTelaCheia() {
  await openFullscreen(conteudo, { texto: 'Conteúdo em tela cheia.' }, { title: 'Tela cheia' })
  resultado.value = 'Tela cheia fechada.'
}
</script>
