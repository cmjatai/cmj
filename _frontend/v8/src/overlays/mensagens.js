import { lerJson } from '~@/stores/GlobalStore'
import { NIVEIS } from '~@/overlays/ToastStore'
import { useToast } from '~@/overlays/useToast'

// Mensagens do framework de mensagens do Django, escritas em <script id="v8-messages"> como uma
// lista de { nivel, texto } (V8-OVL-073).
export const ID_MENSAGENS = 'v8-messages'

// A tag de nível do Django pode trazer várias palavras (`extra_tags` e o nível): vale a primeira
// conhecida. `debug` e qualquer outra viram `info`.
export function nivelDaMensagem(nivel) {
  const palavras = typeof nivel === 'string' ? nivel.toLowerCase().split(/\s+/) : []
  for (const palavra of palavras) {
    if (palavra === 'debug') {
      return 'info'
    }
    if (NIVEIS.includes(palavra)) {
      return palavra
    }
  }
  return 'info'
}

// Cria um toast por mensagem e devolve quantos criou. Elemento ausente, JSON inválido, valor que
// não é lista e item sem texto são ignorados.
export function toastsDasMensagens() {
  const mensagens = lerJson(ID_MENSAGENS)
  if (!Array.isArray(mensagens)) {
    return 0
  }
  const toast = useToast()
  let criados = 0
  mensagens.forEach(mensagem => {
    const texto = mensagem?.texto
    if (typeof texto !== 'string' || !texto.trim()) {
      return
    }
    toast[nivelDaMensagem(mensagem.nivel)](texto)
    criados += 1
  })
  return criados
}

export default toastsDasMensagens
