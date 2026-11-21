// Saídas da página, reunidas aqui para que os testes possam substituí-las.

export function ir(url) {
  window.location.assign(url)
}

export function recarregar() {
  window.location.reload()
}

export function abrirNovaAba(url) {
  return window.open(url, '_blank', 'noopener')
}

// Caminho e query da página atual, sem host: é o único retorno aceito no login (V8-HTTP-041).
export function caminhoAtual() {
  return window.location.pathname + window.location.search
}

export default { ir, recarregar, abrirNovaAba, caminhoAtual }
