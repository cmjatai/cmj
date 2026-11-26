# Genia: ementa de emenda coletiva (LOA)

Status: implementado
Última verificação: 2026-11-20 (commit `4d4f9e67b`)
Código principal: `cmj/utils/genia/loa_agrupamento.py`, `cmj/utils/genia/prompts_loa_agrupamento.py`,
`cmj/loa/models/m_agrupamento.py`, `cmj/api/loa/views/agrupamento.py`,
`cmj/api/loa/views/agrupamentoemendaloa.py`, `_templates/v2018/loa/pdf/agrupamento_preview.html`,
`_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js`
Testes: `cmj/utils/genia/test_genia.py`, `cmj/loa/tests/test_agrupamento_ia.py`

## Escopo

`IAEmentaEmendaColetiva`: consolida as finalidades de várias emendas em um parágrafo, usado como
finalidade de um agrupamento. As regras do agrupamento estão em `docs/specs/loa/fases-emenda.md`.

## Regras

- GENIA-LOA-001 [implementado] O serviço chama o modelo fixo `gemini-3.1-flash-lite` com temperatura
  0 e os demais parâmetros no padrão da API, sem system instruction. É isento de cota: não consulta
  nem registra `IAQuota`. Evidência: `cmj/utils/genia/loa_agrupamento.py:29-38`. Teste:
  `test_ementa_coletiva_usa_modelo_fixo_sem_cota`.
- GENIA-LOA-003 [implementado] O prompt em uso é `PROMPT_V1`, com as finalidades limpas por
  `clean_text`, uma por linha, prefixadas com `- `. `PROMPT_V0` é histórico. Evidência:
  `cmj/utils/genia/loa_agrupamento.py:40-50`, `cmj/utils/genia/prompts_loa_agrupamento.py:31`.
- GENIA-LOA-002 [implementado] Sem finalidades, devolve texto vazio sem chamar a API. Um erro da API
  é registrado em log e levanta `IAEmentaEmendaColetivaError`, cuja mensagem é exibida ao usuário
  (GENIA-LOA-006). Evidência: `cmj/utils/genia/loa_agrupamento.py:10-20`,
  `cmj/utils/genia/loa_agrupamento.py:52-70`. Teste:
  `test_ementa_coletiva_sem_ementas_devolve_vazio_e_erro_levanta`.
- GENIA-LOA-004 [implementado] `Agrupamento.update_finalidade_com_ia` grava o resultado em
  `finalidade`. Se as emendas não tiverem a mesma unidade e entidade, limpa a finalidade e levanta
  `ValueError` sem chamar a I.A. Se a I.A. falhar, limpa a finalidade e repassa o erro. A finalidade
  digitada pelo editor é tratada à parte (LOA-AGR-053 de `docs/specs/loa/edicao-agrupamento.md`): na
  inclusão e na remoção de emenda a I.A. não é chamada, e a falha da I.A. no Ctrl+clique a mantém.
  Evidência:
  `cmj/loa/models/m_agrupamento.py:200-244`. Teste: `test_update_finalidade_limpa_e_repassa_erro`.
- GENIA-LOA-005 [implementado] Na preparação da emenda coletiva, a finalidade automática só é gerada
  quando o agrupamento não tem finalidade própria, uma vez por grupo de unidade e entidade. Na
  prévia, a falha da I.A. deixa a finalidade automática vazia e grava o aviso em `aviso_finalidade`.
  Na geração das emendas coletivas, a falha interrompe a operação antes de criar qualquer emenda.
  Evidência: `cmj/loa/models/m_agrupamento.py:305-317`. Testes: `test_previa_marca_aviso`,
  `test_geracao_da_coletiva_interrompe_com_mensagem`.
- GENIA-LOA-006 [implementado] O usuário é informado da falha da I.A. em cada fluxo:
  - geração manual da finalidade (Ctrl+clique no campo): resposta 400 com a mensagem, exibida como
    mensagem suspensa da tela (LOA-AGR-090). O campo volta ao texto gravado. Evidência: `cmj/api/loa/views/agrupamento.py:134-136`. Teste:
    `test_geracao_manual_responde_400_com_mensagem`.
  - inclusão e remoção de emenda: a operação é concluída e a resposta traz `aviso_finalidade` e a
    finalidade atualizada (`agrupamento_finalidade`), e a tela exibe o aviso como mensagem suspensa
    (LOA-AGR-090). Unidades ou
    entidades diferentes só geram aviso quando apagam uma finalidade digitada (LOA-AGR-053). Na remoção, a finalidade é gerada depois de a emenda sair
    do agrupamento. Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:59-86`,
    `cmj/api/loa/views/agrupamentoemendaloa.py:129`,
    `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:403`,
    `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:498`. Testes:
    `test_inclusao_conclui_e_avisa`, `test_inclusao_sem_erro_devolve_finalidade_gerada`,
    `test_remocao_conclui_e_avisa`, `test_remocao_gera_finalidade_sem_a_emenda_removida`.
  - prévia em PDF: faixa vermelha com o aviso. Evidência:
    `_templates/v2018/loa/pdf/agrupamento_preview.html:40-44`.
  - geração das emendas coletivas: resposta 400 com a mensagem, exibida como mensagem suspensa
    (LOA-AGR-090). Evidência:
    `cmj/api/loa/views/agrupamento.py:143-160`. Teste:
    `test_geracao_da_coletiva_interrompe_com_mensagem`.

## Decisões

- D1. O serviço continua isento de cota, com modelo fixo no código (GENIA-LOA-001). Desde
  LOA-AGR-003, todo fluxo que chama a I.A. exige `emendaloa_full_editor`, inclusive a prévia do
  agrupamento.
- D2. Erro da I.A. é informado ao usuário em vez de virar finalidade vazia sem aviso
  (GENIA-LOA-002). A geração manual da finalidade e a geração das emendas coletivas respondem com
  erro e a mensagem. Na inclusão e na remoção de emenda, a operação é concluída e a resposta traz um
  aviso. Na prévia, o PDF mostra uma faixa de aviso.

## Fora do escopo

Fases, agrupamento e geração das emendas coletivas.
