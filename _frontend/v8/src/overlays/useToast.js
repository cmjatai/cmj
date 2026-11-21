import pinia from '~@/core/pinia'
import { useToastStore } from '~@/overlays/ToastStore'

// Toasts (V8-OVL-070). Funciona dentro e fora de componentes, porque usa o Pinia único da página.
//
//   const toast = useToast()
//   const id = toast.success('Registro salvo.')
//   toast.error('Não foi possível salvar.', { duracao: 10000 })
//   toast.dismiss(id)
//
// `texto` é sempre tratado como texto, nunca como HTML (V8-OVL-104).
export function useToast() {
  const store = useToastStore(pinia)
  const criar = nivel => (texto, opcoes = {}) =>
    store.adicionar({ nivel, texto, duracao: opcoes?.duracao })

  return {
    success: criar('success'),
    info: criar('info'),
    warning: criar('warning'),
    error: criar('error'),
    dismiss: id => store.dispensar(id)
  }
}

export default useToast
