import { describe, expect, it } from 'vitest'

import { HttpError, MENSAGENS_PADRAO, codigoDoStatus, erroDaResposta, normalizarCorpo } from '~@/http/errors'

describe('HttpError e normalização', () => {
  it('V8-HTTP-010: HttpError é um Error com status, codigo, mensagem, campos e gerais', () => {
    const erro = erroDaResposta(400, { nome: ['Obrigatório.'], non_field_errors: ['Datas invertidas.'] })
    expect(erro).toBeInstanceOf(Error)
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.name).toBe('HttpError')
    expect(erro.status).toBe(400)
    expect(erro.codigo).toBe('validacao')
    expect(erro.mensagem).toBe(MENSAGENS_PADRAO.validacao)
    expect(erro.message).toBe(erro.mensagem)
    expect(erro.campos).toEqual({ nome: ['Obrigatório.'] })
    expect(erro.gerais).toEqual(['Datas invertidas.'])
    expect(erro.resposta).toEqual({ nome: ['Obrigatório.'], non_field_errors: ['Datas invertidas.'] })
  })

  it('V8-HTTP-011: cada status tem o seu código', () => {
    expect(codigoDoStatus(400)).toBe('validacao')
    expect(codigoDoStatus(422)).toBe('validacao')
    expect(codigoDoStatus(401)).toBe('nao_autenticado')
    expect(codigoDoStatus(403)).toBe('sem_permissao')
    expect(codigoDoStatus(404)).toBe('nao_encontrado')
    expect(codigoDoStatus(409)).toBe('conflito')
    expect(codigoDoStatus(500)).toBe('servidor')
    expect(codigoDoStatus(503)).toBe('servidor')
    expect(codigoDoStatus(405)).toBe('rede')
    expect(codigoDoStatus(429)).toBe('rede')
  })

  it('V8-HTTP-011: todo código tem mensagem padrão', () => {
    const codigos = ['validacao', 'nao_autenticado', 'sem_permissao', 'nao_encontrado', 'conflito', 'servidor', 'rede', 'cancelada']
    expect(Object.keys(MENSAGENS_PADRAO).sort()).toEqual([...codigos].sort())
    codigos.forEach(codigo => {
      expect(new HttpError({ codigo }).mensagem).toBe(MENSAGENS_PADRAO[codigo])
    })
  })

  it('V8-HTTP-012: o corpo do DRF e o corpo do v8 resultam no mesmo HttpError', () => {
    const drf = erroDaResposta(400, {
      detail: 'Não foi possível salvar.',
      nome: ['Obrigatório.'],
      ementa: ['Muito curta.', 'Sem pontuação.'],
      non_field_errors: ['Datas invertidas.']
    })
    const v8 = erroDaResposta(400, {
      detail: 'Não foi possível salvar.',
      errors: {
        nome: ['Obrigatório.'],
        ementa: ['Muito curta.', 'Sem pontuação.']
      },
      non_field_errors: ['Datas invertidas.']
    })
    const esperado = {
      status: 400,
      codigo: 'validacao',
      mensagem: 'Não foi possível salvar.',
      campos: { nome: ['Obrigatório.'], ementa: ['Muito curta.', 'Sem pontuação.'] },
      gerais: ['Datas invertidas.']
    }
    expect(drf).toMatchObject(esperado)
    expect(v8).toMatchObject(esperado)
    expect(Object.keys(drf.campos)).toEqual(Object.keys(v8.campos))
  })

  it('V8-HTTP-012: erro de campo aninhado vira chave com ponto', () => {
    const drf = normalizarCorpo({ endereco: { cep: ['CEP inválido.'], cidade: { nome: ['Obrigatório.'] } } })
    const v8 = normalizarCorpo({ detail: '', errors: { endereco: { cep: ['CEP inválido.'], cidade: { nome: ['Obrigatório.'] } } } })
    const campos = { 'endereco.cep': ['CEP inválido.'], 'endereco.cidade.nome': ['Obrigatório.'] }
    expect(drf.campos).toEqual(campos)
    expect(v8.campos).toEqual(campos)
  })

  it('V8-HTTP-012: erro em lista de objetos usa o índice', () => {
    const { campos } = normalizarCorpo({ itens: [{}, { nome: ['Obrigatório.'] }, { valor: { moeda: 'Inválida.' } }] })
    expect(campos).toEqual({
      'itens.1.nome': ['Obrigatório.'],
      'itens.2.valor.moeda': ['Inválida.']
    })
  })

  it('V8-HTTP-012: texto solto vale como lista de um item', () => {
    const { campos, gerais } = normalizarCorpo({ nome: 'Obrigatório.', non_field_errors: 'Datas invertidas.' })
    expect(campos).toEqual({ nome: ['Obrigatório.'] })
    expect(gerais).toEqual(['Datas invertidas.'])
  })

  it('V8-HTTP-012: __all__ do formulário Django e erro geral de objeto aninhado', () => {
    const { campos, gerais } = normalizarCorpo({
      detail: 'Corrija os erros.',
      errors: { __all__: ['Período fechado.'], endereco: { non_field_errors: ['Endereço incompleto.'] } },
      non_field_errors: ['Datas invertidas.']
    })
    expect(gerais).toEqual(['Datas invertidas.', 'Período fechado.'])
    expect(campos).toEqual({ endereco: ['Endereço incompleto.'] })
  })

  it('V8-HTTP-012: lista de mensagens na raiz vai para gerais', () => {
    const erro = erroDaResposta(400, ['Operação inválida.'])
    expect(erro.gerais).toEqual(['Operação inválida.'])
    expect(erro.campos).toEqual({})
  })

  it('V8-HTTP-012: mensagem é o detail, ou a padrão do código quando não há detail', () => {
    expect(erroDaResposta(403, { detail: 'Somente a mesa diretora.' }).mensagem).toBe('Somente a mesa diretora.')
    expect(erroDaResposta(403, { detail: 'Somente a mesa diretora.' }).campos).toEqual({})
    expect(erroDaResposta(404, null).mensagem).toBe(MENSAGENS_PADRAO.nao_encontrado)
    expect(erroDaResposta(409, {}).mensagem).toBe(MENSAGENS_PADRAO.conflito)
  })

  it('V8-HTTP-012: corpo que não é JSON não vira mensagem nem campo', () => {
    const erro = erroDaResposta(500, '<h1>Server Error (500)</h1>')
    expect(erro.mensagem).toBe(MENSAGENS_PADRAO.servidor)
    expect(erro.campos).toEqual({})
    expect(erro.gerais).toEqual([])
    expect(erro.resposta).toBe('<h1>Server Error (500)</h1>')
  })
})
