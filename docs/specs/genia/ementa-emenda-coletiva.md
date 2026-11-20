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

## Decisões

- D1. O serviço continua isento de cota, com modelo fixo no código (GENIA-LOA-001).
- D2. Erro da I.A. é informado ao usuário em vez de virar finalidade vazia sem aviso
  (GENIA-LOA-002). A geração manual da finalidade e a geração das emendas coletivas respondem com
  erro e a mensagem. Na inclusão e na remoção de emenda, a operação é concluída e a resposta traz um
  aviso. Na prévia, o PDF mostra uma faixa de aviso.

## Fora do escopo

Fases, agrupamento e geração das emendas coletivas.
