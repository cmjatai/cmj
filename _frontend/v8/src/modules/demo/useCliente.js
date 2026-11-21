import { ref, shallowRef, toValue, watch } from 'vue'
import { obter } from '~@/modules/demo/api'

// Carrega um cliente da API da demo, já na criação do componente e de novo quando o id muda.
//
//   const { cliente, carregando, erro, carregar } = useCliente(() => props.id)
//
// `erro` é o HttpError da última tentativa, ou null. `carregar` serve ao "Tentar de novo".
export function useCliente(id) {
  const cliente = ref(null)
  const carregando = ref(false)
  const erro = shallowRef(null)
  // Só a resposta do pedido mais recente vale: o id pode mudar com um pedido em curso.
  let pedido = 0

  async function carregar() {
    pedido += 1
    const atual = pedido
    cliente.value = null
    erro.value = null
    carregando.value = true
    try {
      const resposta = await obter(toValue(id))
      if (atual === pedido) {
        cliente.value = resposta
      }
    } catch (falha) {
      if (atual === pedido) {
        erro.value = falha
      }
    } finally {
      if (atual === pedido) {
        carregando.value = false
      }
    }
  }

  watch(() => toValue(id), carregar, { immediate: true })

  return { cliente, carregando, erro, carregar }
}
