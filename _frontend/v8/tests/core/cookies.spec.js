import { afterEach, describe, expect, it, vi } from 'vitest'

import { gravarCookieV8, lerCookie } from '~@/core/cookies'

const URL_INICIAL = window.location.href

// O jsdom do Vitest fica em `globalThis.jsdom`: é o único jeito de trocar o protocolo da página.
function irPara(url) {
  globalThis.jsdom.reconfigure({ url: new URL(url, URL_INICIAL).href })
}

// A limpeza de tests/setup.js usa Path=/ e não alcança os cookies gravados com Path=/v8/.
function limparCookiesV8() {
  irPara('/v8/')
  document.cookie.split(';').forEach(c => {
    const nome = c.split('=')[0].trim()
    if (nome) document.cookie = `${nome}=; Max-Age=0; Path=/v8/`
  })
  irPara(URL_INICIAL)
}

describe('cookies do v8', () => {
  afterEach(() => {
    limparCookiesV8()
  })

  it('V8-ARQ-004: o cookie é gravado com Path=/v8/', () => {
    const gravacao = vi.spyOn(document, 'cookie', 'set')

    gravarCookieV8('v8_tema', 'escuro')

    expect(gravacao).toHaveBeenCalledTimes(1)
    expect(gravacao).toHaveBeenCalledWith(
      'v8_tema=escuro; Path=/v8/; Max-Age=31536000; SameSite=Lax'
    )
  })

  it('V8-ARQ-004: o cookie só é visível sob /v8/', () => {
    gravarCookieV8('v8_sidebar', 'recolhida')

    // A página do teste fica em "/", fora do Path do cookie.
    expect(lerCookie('v8_sidebar')).toBeNull()

    irPara('/v8/demo/')
    expect(lerCookie('v8_sidebar')).toBe('recolhida')

    irPara('/v6/')
    expect(lerCookie('v8_sidebar')).toBeNull()
  })

  it.each([
    'tema',
    'sessionid',
    'csrftoken',
    'xv8_tema',
    'V8_tema',
    'v8_',
    'v8_tema; Path=/',
    '',
    null,
    undefined
  ])('V8-ARQ-004: nome que não começa por v8_ é recusado (%s)', nome => {
    const gravacao = vi.spyOn(document, 'cookie', 'set')

    expect(() => gravarCookieV8(nome, 'x')).toThrow()

    expect(gravacao).not.toHaveBeenCalled()
  })

  it('V8-ARQ-004: lerCookie devolve null quando o cookie não existe', () => {
    irPara('/v8/')

    expect(lerCookie('v8_tema')).toBeNull()

    gravarCookieV8('v8_tema', 'claro')
    expect(lerCookie('v8_tema')).toBe('claro')
    // Nome que é só o final de outro não casa.
    expect(lerCookie('tema')).toBeNull()
    expect(lerCookie('v8_te')).toBeNull()
  })

  it('V8-ARQ-067: o cookie tem SameSite=Lax e, em https, Secure', () => {
    const gravacao = vi.spyOn(document, 'cookie', 'set')

    gravarCookieV8('v8_tema', 'claro')
    expect(gravacao).toHaveBeenLastCalledWith(
      'v8_tema=claro; Path=/v8/; Max-Age=31536000; SameSite=Lax'
    )

    irPara('https://localhost:3000/v8/')
    try {
      gravarCookieV8('v8_tema', 'escuro')
      expect(gravacao).toHaveBeenLastCalledWith(
        'v8_tema=escuro; Path=/v8/; Max-Age=31536000; SameSite=Lax; Secure'
      )
      expect(lerCookie('v8_tema')).toBe('escuro')
    } finally {
      document.cookie = 'v8_tema=; Max-Age=0; Path=/v8/; Secure'
    }
  })

  it('V8-ARQ-067: o valor não consegue acrescentar atributos ao cookie', () => {
    const gravacao = vi.spyOn(document, 'cookie', 'set')

    gravarCookieV8('v8_tema', 'escuro; Path=/; Domain=exemplo.com')

    const escrito = gravacao.mock.calls[0][0]
    expect(escrito.match(/Path=/g)).toHaveLength(1)
    expect(escrito).not.toContain('Domain=')
    expect(escrito.endsWith('; Path=/v8/; Max-Age=31536000; SameSite=Lax')).toBe(true)
  })
})
