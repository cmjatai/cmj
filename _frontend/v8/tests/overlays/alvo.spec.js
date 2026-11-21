import { describe, expect, it } from 'vitest'
import { interpretarAlvo, resolverAlvo, urlDoFragmento } from '~@/overlays/alvo'

const registro = {
  cliente: {
    componente: () => Promise.resolve({}),
    props: arg => ({ id: Number(arg) }),
    opcoes: { side: 'right' }
  }
}

describe('alvos de overlay', () => {
  it('V8-OVL-081: reconhece nome com argumento, fragmento e elemento', () => {
    expect(interpretarAlvo('cliente:42')).toEqual({ tipo: 'nome', nome: 'cliente', arg: '42' })
    expect(interpretarAlvo('frag:demo/cliente/42/historico')).toEqual({
      tipo: 'frag',
      caminho: 'demo/cliente/42/historico'
    })
    expect(interpretarAlvo('el:#demo-filtros')).toEqual({ tipo: 'el', id: 'demo-filtros' })
  })

  it('V8-OVL-100: o valor nunca é aceito como URL', () => {
    const hostis = [
      'https://exemplo.invalid/x',
      '//exemplo.invalid/x',
      'frag:https://exemplo.invalid',
      'frag://exemplo.invalid/x',
      'frag:../../admin',
      'frag:demo/../../x',
      'frag:/demo',
      'frag:demo/',
      'frag:demo?x=1',
      'frag:demo#x',
      'frag:demo cliente',
      'el:body',
      'el:#a b',
      'el:#a,script',
      'javascript:alert(1)',
      'Cliente:1',
      '',
      null,
      undefined,
      42
    ]
    hostis.forEach(valor => expect(interpretarAlvo(valor), String(valor)).toBeNull())
  })

  it('V8-OVL-100: o fragmento fica sempre sob a base de fragmentos', () => {
    expect(urlDoFragmento('demo/cliente/7/historico')).toBe('/v8/_frag/demo/cliente/7/historico/')
    expect(urlDoFragmento('demo/x', '/v8/_frag/')).toBe('/v8/_frag/demo/x/')
    expect(urlDoFragmento('../x')).toBeNull()
    expect(urlDoFragmento('https://exemplo.invalid')).toBeNull()
  })

  it('V8-OVL-100: nome fora do registro é ignorado', () => {
    expect(resolverAlvo('pedido:1', registro)).toBeNull()
    expect(resolverAlvo('constructor:1', registro)).toBeNull()
    expect(resolverAlvo('toString', registro)).toBeNull()
  })

  it('V8-OVL-050: nome do registro vira componente com props do argumento', () => {
    const resolvido = resolverAlvo('cliente:42', registro)
    expect(resolvido.conteudo.componente).toBe(registro.cliente.componente)
    expect(resolvido.conteudo.props).toEqual({ id: 42 })
    expect(resolvido.opcoes).toEqual({ side: 'right' })
    expect(resolverAlvo('frag:demo/x', registro).conteudo).toEqual({ frag: 'demo/x' })
  })
})
