// Cookies do v8 (V8-ARQ-004 e V8-ARQ-067).
//
// Todo cookie criado pelo frontend tem nome iniciado por `v8_` e `Path=/v8/`, de modo que nunca é
// enviado às rotas do portal fora de `/v8/`. Eles guardam só preferências de tela.

const NOME_VALIDO = /^v8_[A-Za-z0-9_]+$/
const UM_ANO = 31536000

export function lerCookie(nome) {
  const prefixo = `${nome}=`
  const partes = document.cookie ? document.cookie.split(';') : []
  for (const parte of partes) {
    const item = parte.trim()
    if (item.startsWith(prefixo)) {
      const valor = item.slice(prefixo.length)
      try {
        return decodeURIComponent(valor)
      } catch {
        return valor
      }
    }
  }
  return null
}

export function gravarCookieV8(nome, valor) {
  if (!NOME_VALIDO.test(String(nome))) {
    throw new Error(`Cookie do v8 precisa de nome iniciado por "v8_": ${nome}`)
  }
  let cookie = `${nome}=${encodeURIComponent(valor)}; Path=/v8/; Max-Age=${UM_ANO}; SameSite=Lax`
  if (window.location.protocol === 'https:') {
    cookie += '; Secure'
  }
  document.cookie = cookie
  return cookie
}

export default { lerCookie, gravarCookieV8 }
