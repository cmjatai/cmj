# Genia: ementa de emenda coletiva (LOA)

Status: implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/loa_agrupamento.py`, `cmj/utils/genia/prompts_loa_agrupamento.py`,
`cmj/loa/models/m_agrupamento.py`
Testes: `cmj/utils/genia/test_genia.py`

## Escopo

`IAEmentaEmendaColetiva`: consolida as finalidades de várias emendas em um parágrafo, usado como
finalidade de um agrupamento. As regras do agrupamento estão em `docs/specs/loa/fases-emenda.md`.

## Regras

- GENIA-LOA-001 [implementado] O serviço chama o modelo fixo `gemini-3.1-flash-lite` com temperatura
  0 e os demais parâmetros no padrão da API, sem system instruction. É isento de cota: não consulta
  nem registra `IAQuota`. Evidência: `cmj/utils/genia/loa_agrupamento.py:17-26`.
- GENIA-LOA-003 [implementado] O prompt em uso é `PROMPT_V1`, com as finalidades limpas por
  `clean_text`, uma por linha, prefixadas com `- `. `PROMPT_V0` é histórico. Evidência:
  `cmj/utils/genia/loa_agrupamento.py:28-38`, `cmj/utils/genia/prompts_loa_agrupamento.py:31`.
- GENIA-LOA-002 [implementado] Sem finalidades, devolve texto vazio sem chamar a API. Qualquer erro
  da API é registrado em log e também devolve texto vazio. Evidência:
  `cmj/utils/genia/loa_agrupamento.py:40-54`.
- GENIA-LOA-004 [observado] `Agrupamento.update_finalidade_com_ia` grava o resultado em `finalidade`.
  Se as emendas não tiverem a mesma unidade e entidade, limpa a finalidade e levanta `ValueError` sem
  chamar a I.A. Evidência: `cmj/loa/models/m_agrupamento.py:149-178`.
- GENIA-LOA-005 [observado] Na preparação da emenda coletiva, a finalidade automática só é gerada
  quando o agrupamento não tem finalidade própria, uma vez por grupo de unidade e entidade.
  Evidência: `cmj/loa/models/m_agrupamento.py:237-248`.

## Dúvidas

- D1. O serviço não tem limite de cota e usa um modelo fixo no código. Cada prévia de emenda coletiva
  sem finalidade própria chama a API uma vez por grupo (GENIA-LOA-005). Colocar sob cota exige uma
  chave nova em `IAQuota.ServicosAutorizados`, com migration, e uma cota configurada no admin antes do
  deploy, ou a geração passa a devolver vazio. Fazer?
- D2. Erro da I.A. vira finalidade vazia, sem aviso ao usuário (GENIA-LOA-002). Ele deve ser
  informado?

## Fora do escopo

Fases, agrupamento e geração das emendas coletivas.
