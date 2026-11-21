import pinia from '~@/core/pinia'
import navegacao from '~@/core/navegacao'
import { telaLarga } from '~@/core/media'
import { modais } from '~@/core/modais'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { interpretarAlvo, resolverAlvo } from '~@/overlays/alvo'
import { abrirPainel, podeAbrirPainel } from '~@/overlays/urlSync'

// Gatilhos declarados em HTML (V8-OVL-080 a 085). Um ouvinte de clique e um de envio, no
// documento, atendem data-drawer, data-modal e data-confirm, inclusive em HTML inserido depois.
// Quando o alvo não pode ser aberto, o clique segue como navegação normal.

let registroDeModais = modais

function opcoesDoDrawer(elemento) {
  if (!elemento) {
    return {}
  }
  const dados = elemento.dataset
  const opcoes = {}
  if (dados.drawerSide) opcoes.side = dados.drawerSide
  if (dados.drawerSize) opcoes.size = dados.drawerSize
  if (dados.drawerMode) opcoes.mode = dados.drawerMode
  if (dados.drawerModeEstreito) opcoes.modeEstreito = dados.drawerModeEstreito
  if (dados.drawerTitle) opcoes.title = dados.drawerTitle
  if (dados.drawerScrim === 'false') opcoes.scrim = false
  return opcoes
}

// Abre o elemento da página como drawer. As opções vêm do próprio elemento e do gatilho.
export function abrirElemento(id, opcoesDoGatilho = {}, gatilho = null) {
  const store = useOverlayStore(pinia)
  const chave = `el:#${id}`
  const elemento = document.getElementById(id)
  if (!elemento) {
    return false
  }
  if (!store.entradas.some(e => e.chave === chave)) {
    const opcoes = { ...opcoesDoDrawer(elemento), ...opcoesDoGatilho }
    if (!opcoes.title && gatilho) {
      opcoes.title = gatilho.textContent.trim()
    }
    store.openDrawer({ el: id }, { ...opcoes, chave, gatilho })
  }
  return true
}

function abrirDrawer(gatilho) {
  const alvo = interpretarAlvo(gatilho.dataset.drawer)
  if (!alvo) {
    return false
  }
  const opcoes = opcoesDoDrawer(gatilho)
  if (alvo.tipo === 'el') {
    return abrirElemento(alvo.id, opcoes, gatilho)
  }
  // O título do fragmento vem dele mesmo; até chegar, vale o texto do gatilho (V8-OVL-042).
  if (!opcoes.title && alvo.tipo === 'frag') {
    opcoes.title = gatilho.textContent.trim()
  }
  // Painel e fragmento ficam na URL. Valor que o registro não conhece segue como link comum.
  const texto = gatilho.dataset.drawer.trim()
  if (!podeAbrirPainel(texto)) {
    return false
  }
  abrirPainel(texto, opcoes)
  return true
}

function abrirModal(gatilho) {
  const resolvido = resolverAlvo(gatilho.dataset.modal, registroDeModais)
  if (!resolvido || resolvido.alvo.tipo === 'el') {
    return false
  }
  const store = useOverlayStore(pinia)
  const opcoes = { ...resolvido.opcoes }
  if (gatilho.dataset.modalTitle) opcoes.title = gatilho.dataset.modalTitle
  if (gatilho.dataset.modalSize) opcoes.size = gatilho.dataset.modalSize
  if (resolvido.alvo.tipo === 'frag') {
    store.abrir({
      kind: 'modal',
      conteudo: resolvido.conteudo,
      opcoes: { title: gatilho.textContent.trim(), ...opcoes }
    })
  } else {
    store.openModal(resolvido.conteudo.componente, resolvido.conteudo.props, opcoes)
  }
  return true
}

function confirmar(fonte) {
  const dados = fonte.dataset
  return useOverlayStore(pinia).confirm({
    mensagem: dados.confirm || 'Confirma esta ação?',
    titulo: dados.confirmTitle || 'Confirmar',
    rotuloOk: dados.confirmOk || 'Confirmar',
    rotuloCancelar: dados.confirmCancel || 'Cancelar',
    variante: dados.confirmVariant || (fonte.classList.contains('v8-btn-perigo') ? 'perigo' : 'padrao')
  })
}

function enviaFormulario(elemento) {
  if (!elemento.form) {
    return false
  }
  const tipo = (elemento.getAttribute('type') || (elemento.tagName === 'BUTTON' ? 'submit' : '')).toLowerCase()
  return tipo === 'submit' || tipo === 'image'
}

function aoClicar(evento) {
  // Clique com tecla modificadora ou outro botão segue o caminho normal (V8-OVL-085).
  if (evento.defaultPrevented || evento.button !== 0 ||
      evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
    return
  }
  const gatilho = evento.target.closest?.('[data-drawer], [data-modal], [data-confirm]')
  if (!gatilho) {
    return
  }
  if (gatilho.hasAttribute('data-drawer')) {
    if (abrirDrawer(gatilho)) {
      evento.preventDefault()
    }
    return
  }
  if (gatilho.hasAttribute('data-modal')) {
    if (abrirModal(gatilho)) {
      evento.preventDefault()
    }
    return
  }
  // data-confirm em formulário ou em botão de envio é tratado no envio.
  if (gatilho.tagName === 'FORM' || enviaFormulario(gatilho)) {
    return
  }
  if (gatilho.dataset.v8Confirmado) {
    delete gatilho.dataset.v8Confirmado
    return
  }
  evento.preventDefault()
  confirmar(gatilho).then(confirmado => {
    if (!confirmado) {
      return
    }
    if (gatilho.tagName === 'A' && gatilho.href) {
      navegacao.ir(gatilho.href)
    } else {
      gatilho.dataset.v8Confirmado = '1'
      gatilho.click()
    }
  })
}

function aoEnviar(evento) {
  const formulario = evento.target
  if (!formulario || formulario.tagName !== 'FORM') {
    return
  }
  const botao = evento.submitter || null
  const fonte = botao?.hasAttribute('data-confirm')
    ? botao
    : (formulario.hasAttribute('data-confirm') ? formulario : null)
  if (!fonte) {
    return
  }
  if (formulario.dataset.v8Confirmado) {
    delete formulario.dataset.v8Confirmado
    return
  }
  evento.preventDefault()
  confirmar(fonte).then(confirmado => {
    if (!confirmado) {
      return
    }
    formulario.dataset.v8Confirmado = '1'
    if (formulario.requestSubmit) {
      formulario.requestSubmit(botao || undefined)
    } else {
      formulario.submit()
    }
  })
}

// Elementos com data-drawer-auto abrem sozinhos em tela larga, como um painel fixo de filtros.
export function abrirAutomaticos(raiz = document) {
  if (!telaLarga()) {
    return
  }
  raiz.querySelectorAll('[data-drawer-auto][id]').forEach(elemento => abrirElemento(elemento.id))
}

export function iniciarGatilhos(opcoes = {}) {
  registroDeModais = opcoes.modais || modais
  document.addEventListener('click', aoClicar)
  document.addEventListener('submit', aoEnviar)
  abrirAutomaticos()
  return () => {
    document.removeEventListener('click', aoClicar)
    document.removeEventListener('submit', aoEnviar)
  }
}
