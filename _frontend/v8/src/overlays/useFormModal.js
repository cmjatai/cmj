import { nextTick, ref, watch } from 'vue'
import { HttpError } from '~@/http/client'
import { useOverlay } from '~@/overlays/useOverlay'

// Formulário dentro de um modal, ligado aos erros de validação do Django (V8-OVL-064 e 065).
//
//   const valores = reactive({ nome: '', email: '' })
//   const { erros, gerais, enviando, submeter, erroDe } = useFormModal({
//     valores,
//     enviar: dados => http.put(url, dados)
//   })
//
// `submeter` vai no @submit.prevent do <form>. Em erro de validação o modal continua aberto,
// `erros` recebe as mensagens por campo e `gerais` as que não são de um campo. Em sucesso o
// modal fecha e a Promise de quem o abriu resolve com a resposta.
export function useFormModal({ valores, enviar }) {
  const overlay = useOverlay()
  const erros = ref({})
  const gerais = ref([])
  const enviando = ref(false)

  // O primeiro campo editado marca o modal como alterado.
  watch(valores, () => overlay.setDirty(true), { deep: true })

  async function submeter(evento) {
    if (enviando.value) {
      return
    }
    const formulario = evento?.target?.closest?.('form') || null
    enviando.value = true
    erros.value = {}
    gerais.value = []
    try {
      const resposta = await enviar({ ...valores })
      overlay.setDirty(false)
      overlay.close(resposta === undefined ? true : resposta)
    } catch (falha) {
      if (falha instanceof HttpError && falha.codigo === 'validacao') {
        erros.value = falha.campos || {}
        gerais.value = falha.gerais || []
        if (!Object.keys(erros.value).length && !gerais.value.length) {
          gerais.value = [falha.mensagem]
        }
      } else {
        gerais.value = [falha?.mensagem || 'Não foi possível salvar. Tente de novo.']
      }
      await nextTick()
      formulario?.querySelector('[aria-invalid="true"]')?.focus()
    } finally {
      enviando.value = false
    }
  }

  return {
    erros,
    gerais,
    enviando,
    submeter,
    erroDe: campo => erros.value[campo]?.[0] || ''
  }
}
