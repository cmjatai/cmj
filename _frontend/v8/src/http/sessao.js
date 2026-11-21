// Fluxo de sessão expirada (docs/specs/v8/http.md, V8-HTTP-020 a 025 e 041 a 043).
//
// O cliente chama tratarFalhaDeSessao() ao receber 401 ou 403. Se a sessão expirou numa página
// carregada com usuário, a requisição fica pendente enquanto um único modal pede que o usuário
// entre de novo pela tela /login/, em outra aba. O v8 não pede, não envia e não guarda credencial.
import http from './client'
import { erroCancelada, erroDaResposta, erroNaoAutenticado } from './errors'
import { caminhoAtual, ir, recarregar } from '~@/core/navegacao'
import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useGlobalStore } from '~@/stores/GlobalStore'

// Requisições à espera da reautenticação.
const pendentes = []

// null: nada em curso. 'modal': o modal está aberto. 'saindo': a página está indo embora, e uma
// nova falha de sessão rejeita direto em vez de abrir outro modal.
let fase = null

// 401 é sessão expirada. 403 só é se /api/version disser que não há usuário (V8-HTTP-020).
async function sessaoExpirou(status) {
  if (status === 401) {
    return true
  }
  try {
    const versao = await http.get(useGlobalStore(pinia).urls.versao, { semSessao: true })
    return !versao?.is_authenticated
  } catch {
    // Sem resposta não há como afirmar que a sessão expirou: vale o 403 recebido.
    return false
  }
}

function mesmoUsuario(versao, usuario) {
  const novo = versao?.is_authenticated ? versao.user?.id : null
  const atual = usuario?.id
  if (novo === null || novo === undefined || atual === null || atual === undefined) {
    return false
  }
  return String(novo) === String(atual)
}

function soltar(pendente) {
  if (pendente.signal) {
    pendente.signal.removeEventListener('abort', pendente.aoCancelar)
  }
}

function retirarPendentes() {
  const fila = pendentes.splice(0)
  fila.forEach(soltar)
  return fila
}

function rejeitar(fila) {
  fila.forEach(pendente => pendente.reject(erroNaoAutenticado(pendente.status, pendente.corpo)))
}

// Decide o que fazer com as pendentes depois que o modal fecha. Ao entrar, `fase` é 'saindo'.
async function aposOModal(resultado, fila) {
  const overlay = useOverlayStore(pinia)
  const global = useGlobalStore(pinia)

  if (resultado?.retomar) {
    if (!mesmoUsuario(resultado.versao, global.usuario)) {
      // Outro usuário entrou: nada do que estava pendente é refeito em nome dele (V8-HTTP-042).
      rejeitar(fila)
      recarregar()
      return
    }
    useAuthStore(pinia).aplicarVersao(resultado.versao)
    fase = null
    // Cada pendente é refeita uma única vez: se a sessão falhar de novo, ela rejeita (V8-HTTP-023).
    fila.forEach(pendente => pendente.refazer().then(pendente.resolve, pendente.reject))
    return
  }

  // Modal dispensado ou "Ir para o login" (V8-HTTP-024).
  rejeitar(fila)
  if (overlay.temAlteracoes) {
    const podeSair = await overlay.podeDescartar(overlay.entradas.map(e => e.id))
    if (!podeSair) {
      return
    }
  }
  // O retorno vem só do caminho e da query da página atual (V8-HTTP-041).
  ir(global.urls.login + '?next=' + encodeURIComponent(caminhoAtual()))
}

async function conduzirReautenticacao() {
  let resultado
  try {
    resultado = await useOverlayStore(pinia).openModal(
      () => import('~@/http/ModalSessao.vue'),
      {},
      { size: 'sm', title: 'Sessão expirada' }
    )
  } catch {
    // Modal que não abriu vale como modal dispensado.
    resultado = undefined
  }
  fase = 'saindo'
  const fila = retirarPendentes()
  try {
    await aposOModal(resultado, fila)
  } catch {
    // Nenhuma pendente fica sem resposta. Rejeitar a que já foi resolvida não tem efeito.
    rejeitar(fila)
  } finally {
    if (fase === 'saindo') {
      fase = null
    }
  }
}

function aguardarReautenticacao({ status, corpo, signal, refazer }) {
  return new Promise((resolve, reject) => {
    const pendente = { status, corpo, signal, refazer, resolve, reject, aoCancelar: null }
    if (signal) {
      // Cancelar uma requisição pendente a tira da fila sem esperar o modal (V8-HTTP-007).
      pendente.aoCancelar = () => {
        const posicao = pendentes.indexOf(pendente)
        if (posicao !== -1) {
          pendentes.splice(posicao, 1)
        }
        reject(erroCancelada())
      }
      signal.addEventListener('abort', pendente.aoCancelar, { once: true })
    }
    pendentes.push(pendente)
    if (fase !== 'modal') {
      // Um único modal para todas as requisições nessa situação (V8-HTTP-021).
      fase = 'modal'
      conduzirReautenticacao()
    }
  })
}

// Chamado pelo cliente quando a resposta é 401 ou 403. Devolve o resultado da requisição refeita
// ou rejeita com HttpError.
//   status, corpo: a resposta que falhou
//   refeita: true quando esta já é a segunda tentativa da mesma requisição
//   refazer: função que repete a requisição
export async function tratarFalhaDeSessao({ status, corpo = null, refeita = false, signal = null, refazer }) {
  if (!(await sessaoExpirou(status))) {
    throw erroDaResposta(status, corpo)
  }
  // Página carregada como anônimo não tem sessão a retomar (V8-HTTP-025).
  if (!useGlobalStore(pinia).autenticado || refeita || fase === 'saindo') {
    throw erroNaoAutenticado(status, corpo)
  }
  if (signal?.aborted) {
    throw erroCancelada()
  }
  return aguardarReautenticacao({ status, corpo, signal, refazer })
}

// Só para testes: esquece as pendentes e o modal em curso.
export function reiniciarFluxoDeSessao() {
  retirarPendentes()
  fase = null
}
