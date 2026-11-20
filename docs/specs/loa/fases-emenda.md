# LOA: fases da emenda

Status: implementado
Última verificação: 2026-11-19 (commit `9a51c6f0a`)
Código principal: `cmj/loa/models/m_emendaloa.py`, `cmj/loa/views/v_emendaloa.py`,
`cmj/loa/forms/f_emendaloa.py`, `cmj/loa/models/m_agrupamento.py`, `cmj/api/loa/views/`
Testes: `cmj/loa/tests/test_fases_emenda.py` (`python -m pytest cmj/loa/tests -m spec`)

As regras `[observado]` descrevem o comportamento atual, obtido por leitura do código, sem executar
os fluxos. As regras de negócio confirmadas em 2026-11-19 estão em "Regras acordadas": `[acordado]`
indica que o código já atendia, `[desejado]` indica que ele ainda precisa mudar e `[implementado]`
indica uma regra `[desejado]` já corrigida e coberta por teste. Quando uma regra `[observado]`
conflitar com uma delas, vale a regra acordada: várias regras observadas descrevem o código anterior à
implementação.

## Ordem de implementação

**Os testes vêm antes de qualquer correção.** Não altere código de produção para atender às regras
`[desejado]` antes de concluir a etapa 1.

1. **Testes:** escreva testes para as regras `[acordado]` e `[desejado]`, ligados aos IDs com
   `@pytest.mark.spec("LOA-FASE-NNN")`. O marker precisa ser registrado no `pyproject.toml`, porque o
   projeto usa `--strict-markers`. Testes de `[acordado]` devem passar. Testes de `[desejado]` devem
   falhar, mostrando a divergência atual. Comece por inclusão em agrupamento (LOA-FASE-058 a 060),
   cancelamento de coletiva (056 e 057) e dono da coletiva (064), e siga para as transições e permissões.
2. **Revisão:** apresente o resultado dos testes antes de iniciar as correções.
3. **Implementação:** corrija uma regra ou um grupo pequeno de regras por vez, até o teste passar, e
   marque cada uma como `[implementado]`.

## Escopo

Valores de `EmendaLoa.fase`, transições, histórico e efeitos da fase sobre edição, registro contábil,
agrupamento e proposição.

## Fases

| Valor | Constante | Rótulo |
| --- | --- | --- |
| -10 | `TRANSFORMADA_EM_COLETIVA` | Transformada em Emenda Coletiva |
| 10 | `PROPOSTA` | Proposta Legislativa |
| 12 | `PROPOSTA_LIBERADA` | Proposta Liberada para Edição Contábil |
| 15 | `EDICAO_CONTABIL` | Em edição pela Contabilidade |
| 17 | `LIBERACAO_CONTABIL` | Liberado pela Contabilidade e/ou Aguardando Protocolo |
| 20 | `EM_TRAMITACAO` | Matéria protocolada, em tramitação |
| 25 | `APROVACAO_LEGISLATIVA` | Aprovada no Processo Legislativo |
| 30 | `APROVACAO_LEGAL` | Aprovada |
| 40 | `IMPEDIMENTO_TECNICO` | Impedimento Técnico |
| 50 | `EMENDA_REDEFINIDA` | Emenda Redefinida/Sanada |
| 60 | `EMENDA_EM_EXECUCAO` | Em Execução |
| 99 | `EMENDA_FINALIZADA` | Finalizada |

Evidência: `cmj/loa/models/m_emendaloa.py:70-100`.

## Regras acordadas

### Princípio geral

- LOA-FASE-050 [implementado] O servidor aplica toda regra de fase. Controles do JavaScript ou da tela
  só orientam o usuário, e uma requisição que tente contorná-los é negada. As transições manuais passam
  por `EmendaLoa.transicao_permitida` e `EmendaLoa.criacao_permitida`
  (`cmj/loa/models/m_emendaloa.py:107-118`, `cmj/loa/models/m_emendaloa.py:279-313`), usadas pela API
  e pelo formulário.

### Quem muda cada fase

- LOA-FASE-051 [implementado] O autor só cria emenda na fase 10. Evidência: o formulário limita o select
  e valida em `clean()` (`cmj/loa/forms/f_emendaloa.py:480-482`, `cmj/loa/forms/f_emendaloa.py:552-567`),
  e o POST da API recusa outra fase (`cmj/api/loa/views/emendaloa.py:98-105`).
- LOA-FASE-052 [implementado] O autor pode mudar manualmente de 10 para 12 na edição e voltar de 12 para
  10 enquanto o editor contábil não capturar a emenda (12 → 15). Outras transições do autor são
  recusadas pelo PATCH (`cmj/api/loa/views/emendaloa.py:107-117`) e pelo formulário.
- LOA-FASE-053 [implementado] O editor contábil (`emendaloa_full_editor`, sem ser superusuário) faz as
  transições 12 → 15, 12 → 17, 15 → 17 e 17 → 15. O Operador da LOA segue LOA-FASE-065. Quem é editor
  contábil e operador de autor soma as duas listas. Evidência: `TRANSICOES_EDITOR_CONTABIL`
  (`cmj/loa/models/m_emendaloa.py:112-117`), aplicada no PATCH e no `clean()` do formulário.
- LOA-FASE-054 [implementado] O sistema muda para 20 ao incorporar a proposição associada à emenda na
  matéria (`sapl/materia/forms.py:3418-3422`, sem teste: ver P2). Manualmente, só superusuário e
  Operador da LOA podem escolher essa fase: nenhuma lista de transições de autor ou editor chega a 20.
- LOA-FASE-055 [implementado] Emenda já na fase 20 ou superior só é movimentada por superusuário ou
  Operador da LOA. A tela bloqueia os demais ao abrir a edição acima de 17
  (`cmj/loa/views/v_emendaloa.py:1135-1145`), e o PATCH e o formulário recusam a transição.
- LOA-FASE-062 [acordado] O superusuário usa a mesma tela de edição do autor, sem limitação das fases
  no select. Evidência: `cmj/loa/forms/f_emendaloa.py:472-513`, `cmj/loa/views/v_emendaloa.py:1074-1088`.
- LOA-FASE-063 [implementado] O editor contábil pode devolver para a fase 10, pelo botão "Devolver para
  correção", emendas nas fases 15 ou 17. Evidência: `cmj/loa/views/v_emendaloa.py:1090-1122`.
- LOA-FASE-069 [implementado] Os botões "Concluir edição contábil" (→ 17) e "Devolver para correção"
  (→ 10) só agem sobre emendas nas fases 15 e 17, para qualquer usuário, inclusive o Operador da LOA e
  o superusuário. Em outra fase, o servidor recusa a ação com erro no formulário e mantém a fase.
  Evidência: `FASES_DOS_BOTOES_CONTABEIS` (`cmj/loa/models/m_emendaloa.py:118`),
  `cmj/loa/views/v_emendaloa.py:1090-1122`. Decidido em D13.
- LOA-FASE-065 [acordado] O Operador da LOA acessa e edita a emenda em qualquer fase, vê todas as
  fases no select e pode fazer as transições disponíveis nele. O acesso é identificado pelas permissões
  `add_emendaloa`, `change_emendaloa` e `emendaloa_full_editor` (`EmendaLoa.edita_em_qualquer_fase`).
  A fase -10 continua oculta pelo manager padrão (LOA-FASE-002). Evidência:
  `cmj/loa/models/m_emendaloa.py:279-288`, `cmj/loa/forms/f_emendaloa.py:472-513`,
  `cmj/globalrules/map_rules.py:241-250`.
- LOA-FASE-066 [implementado] A captura automática de 12 para 15 ao abrir a edição vale só para o editor
  contábil. O superusuário abre a emenda sem mudar a fase e só a altera manualmente no formulário.
  Evidência: `cmj/loa/views/v_emendaloa.py:1120-1130`.

### Emenda coletiva

- LOA-FASE-056 [acordado] Ao gerar a coletiva, a emenda de origem passa para -10. Ao cancelar, volta
  para 15. Evidência: `cmj/loa/models/m_agrupamento.py:268-276`, `cmj/loa/models/m_agrupamento.py:313-316`.
- LOA-FASE-057 [implementado] O cancelamento não altera a fase das emendas do agrupamento que não
  estavam em -10. Evidência: a API só chama o model (`cmj/api/loa/views/agrupamento.py:103-115`).
- LOA-FASE-064 [implementado] A emenda coletiva recebe como dono o `owner` da primeira emenda do
  conjunto, `emenda["emendas"][0].owner_id`; a lista segue a ordem por `id`. Evidência:
  `cmj/loa/models/m_agrupamento.py:299-300`.

### Inclusão em agrupamento

- LOA-FASE-058 [implementado] O servidor nega a inclusão de emenda na fase 10. Evidência:
  `cmj/api/loa/views/agrupamentoemendaloa.py:64-90`.
- LOA-FASE-059 [implementado] O servidor aceita apenas emendas que a tela permite incluir: fase 12 ou 15
  e mesmo ano da LOA do agrupamento. Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:64-90`.
- LOA-FASE-060 [implementado] O servidor define a fase resultante da inclusão (15) e ignora
  `emendaloa__fase` enviado pelo cliente. Evidência: `cmj/api/loa/views/agrupamentoemendaloa.py:92-102`.

### Histórico

- LOA-FASE-067 [implementado] `EmendaLoaHistoricoFase.usuario` registra quem mudou a fase. A FK aceita
  vazio, usado nos registros antigos e nas mudanças sem usuário (tasks, shell). Quem muda a fase
  informa o usuário em `EmendaLoa._usuario_fase` antes do `save()`, e o signal consome o atributo para
  que ele não valha no `save()` seguinte. Na criação pela API, o histórico inicial recebe o usuário logo
  após o `save()`. O detalhe da emenda mostra o usuário ao superusuário. Evidência:
  `cmj/loa/models/m_emendaloa.py:1007-1016`, `cmj/loa/signals.py:23-38`,
  `cmj/api/loa/views/emendaloa.py:119-129`, `cmj/loa/forms/f_emendaloa.py:615`,
  `cmj/loa/views/v_emendaloa.py:1131`, `cmj/loa/models/m_agrupamento.py:281-326`,
  `cmj/api/loa/views/agrupamentoemendaloa.py:121`, `cmj/loa/forms/f_agrupamento.py:293-299`,
  `sapl/materia/forms.py:3422`.

### Registros contábeis

- LOA-FASE-068 [implementado] Quem tem permissão para alterar registros contábeis da emenda
  (`emendaloa_full_editor`) pode criar, alterar e excluir esses registros em qualquer fase. Evidência:
  `cmj/api/loa/views/emendaloaregistrocontabil.py:287-299`. Substitui LOA-FASE-040. Decidido em D14.

### Valor

- LOA-FASE-061 [acordado] Emenda com ajuste tem valor computado zero, porque o ajuste assume o papel
  da emenda. Evidência: `cmj/loa/models/m_emendaloa.py:583-590`.

## Regras observadas

### Estado e histórico

- LOA-FASE-001 [observado] Emenda nova tem fase 10 por padrão. Evidência:
  `cmj/loa/models/m_emendaloa.py:125-127`.
- LOA-FASE-002 [observado] `EmendaLoa.objects` e as relações que usam o manager padrão ocultam fases
  menores ou iguais a 0; `all_objects` mostra todas. Evidência:
  `cmj/loa/models/m_emendaloa.py:34-59`, confirmado pelo SQL de `Agrupamento.emendas`.
- LOA-FASE-003 [observado] Cada `save()` cuja fase difere do último histórico cria um registro em
  `EmendaLoaHistoricoFase`, com fase, horário e, quando informado, o usuário (LOA-FASE-067).
  Evidência: `cmj/loa/signals.py:23-38`, `cmj/loa/models/m_emendaloa.py:992-1024`.

### Transições

| ID | De | Para | Gatilho | Quem | Evidência |
| --- | --- | --- | --- | --- | --- |
| LOA-FASE-010 [observado] | 10, 12 | 10, 12 | Campo `fase` no formulário, com autosave por PATCH | Quem não tem `add_emendaloa` nem é editor contábil | `cmj/loa/forms/f_emendaloa.py:472-484`, `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:386-393` |
| LOA-FASE-011 [acordado] | 12 | 15 | Abrir a tela de edição (GET) | Editor contábil (ver LOA-FASE-066) | `cmj/loa/views/v_emendaloa.py:1115-1121` |
| LOA-FASE-012 [observado] | Qualquer | 15, 17 | Campo `fase` no formulário | Editor contábil sem `add_emendaloa` e não superusuário | `cmj/loa/forms/f_emendaloa.py:271-274`, `cmj/loa/forms/f_emendaloa.py:472`, `cmj/loa/forms/f_emendaloa.py:511-513` |
| LOA-FASE-013 [observado] | Qualquer | 17 | Botão "Concluir edição contábil" | `emendaloa_full_editor` | `cmj/loa/views/v_emendaloa.py:1098-1108` |
| LOA-FASE-014 [observado] | Qualquer | 10 | Botão "Devolver para correção" | `emendaloa_full_editor` | `cmj/loa/views/v_emendaloa.py:1098-1108` |
| LOA-FASE-015 [observado] | Busca: menor que 17 | 15 pela interface | Adicionar ao agrupamento, enviando `emendaloa__fase` | `emendaloa_full_editor` | `cmj/api/loa/views/emendaloa.py:341`, `cmj/api/loa/views/agrupamentoemendaloa.py:17-18`, `cmj/api/loa/views/agrupamentoemendaloa.py:68-72`, `_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:361-370` |
| LOA-FASE-016 [observado] | Entre 1 e 16 | 17 | Salvar o agrupamento, incluindo as coletivas geradas | Formulário de agrupamento | `cmj/loa/forms/f_agrupamento.py:290-298` |
| LOA-FASE-017 [observado] | Emenda de origem | -10 | Gerar emenda coletiva | `emendaloa_full_editor` | `cmj/loa/models/m_agrupamento.py:315-318`, `cmj/api/loa/views/agrupamento.py:14-16`, `cmj/api/loa/views/agrupamento.py:79-85` |
| LOA-FASE-018 [observado] | Nova coletiva | 15 | Gerar emenda coletiva | `emendaloa_full_editor` | `cmj/loa/models/m_agrupamento.py:296-313` |
| LOA-FASE-019 [observado] | -10 e emendas visíveis do agrupamento | 15 | Cancelar coletivas; as coletivas geradas são excluídas | `emendaloa_full_editor` | `cmj/loa/models/m_agrupamento.py:268-280`, `cmj/api/loa/views/agrupamento.py:103-113` |
| LOA-FASE-020 [observado] | 17 | 20 | Incorporar proposição como matéria, vinculando a emenda | Fluxo de `ConfirmarProposicaoForm` | `sapl/materia/forms.py:3278-3296`, `sapl/materia/forms.py:3418-3422` |

- LOA-FASE-021 [observado] Só entram na coletiva as emendas com `permite_juncao_coletiva` e sem
  matéria, e só é gerada coletiva para conjuntos de mesma unidade e entidade com mais de uma emenda.
  Evidência: `cmj/loa/models/m_agrupamento.py:188-194`, `cmj/loa/models/m_agrupamento.py:292-294`.
- LOA-FASE-022 [observado] Quem tem `add_emendaloa`, incluindo superusuário e o grupo Operador da LOA,
  vê todas as fases no select, porque as limitações do campo só valem sem essa permissão. Evidência:
  `cmj/loa/forms/f_emendaloa.py:472-513`, `cmj/globalrules/map_rules.py:241-250`.

### Edição

- LOA-FASE-030 [observado] Na tela, operador de autor sem as permissões de LOA-FASE-065 não envia POST quando a fase é
  maior que 12 e diferente de 17. Evidência: `cmj/loa/views/v_emendaloa.py:1082-1096`.
- LOA-FASE-031 [observado] Fora do caso do editor contábil nas fases 12 a 17 e de quem tem as
  permissões de LOA-FASE-065, o GET da edição bloqueia não superusuários em fase maior que 17, usuários de outro autor e a fase 15. Evidência:
  `cmj/loa/views/v_emendaloa.py:1112-1163`.
- LOA-FASE-032 [observado] Para quem não tem `add_emendaloa` nem é editor contábil, fase maior que 12 limita `tipo`, `fase`,
  `unidade` e `entidade` ao valor atual no formulário. Evidência:
  `cmj/loa/forms/f_emendaloa.py:472`, `cmj/loa/forms/f_emendaloa.py:486-509`.
- LOA-FASE-033 [observado] Sem `change_emendaloa`, o PATCH da API exige emenda sem matéria e, ou
  `emendaloa_full_editor`, ou operador de autor participante com fase até 12 ou igual a 17. Com
  `change_emendaloa`, a permissão é concedida antes dessas verificações. Evidência:
  `cmj/api/loa/views/emendaloa.py:29-38`, `cmj/api/loa/views/emendaloa.py:57-81`.
  O "participante" foi substituído pelo autor do dono em LOA-EMD-076 (`docs/specs/loa/edicao-emenda.md`).

### Efeitos em outros fluxos

- LOA-FASE-040 [observado] Registro contábil da emenda só pode ser alterado na fase 15, por
  `emendaloa_full_editor`. Evidência: `cmj/api/loa/views/emendaloaregistrocontabil.py:290-306`.
  Substituída por LOA-FASE-068.
- LOA-FASE-041 [observado] A proposição individual só é gerada na fase 17, e o registro em lote só
  processa emendas nessa fase criadas por operadores do mesmo autor. Evidência:
  `cmj/loa/views/v_emendaloa.py:1312-1317`, `cmj/loa/tasks.py:26-32`.
- LOA-FASE-042 [observado] Emenda na fase -10 não pode ser removida do agrupamento. Evidência:
  `cmj/api/loa/views/agrupamentoemendaloa.py:41-44`.
- LOA-FASE-043 [observado] O total de impedimentos do parlamentar considera emendas que já passaram
  pelas fases 40 ou 50, com base no histórico. Evidência: `cmj/loa/views/v_loa.py:523-535`.
- LOA-FASE-044 [observado] Emenda em impedimento técnico, mesmo sem ajuste, também tem valor computado
  zero. Evidência: `cmj/loa/models/m_emendaloa.py:583-590`.

## Dúvidas

Nenhuma pendente. D13 virou LOA-FASE-069 e D14 virou LOA-FASE-068, ambas decididas em 2026-11-19.

## Pendências encontradas

Problemas vistos ao escrever os testes, fora das regras desta spec. Não bloqueiam a implementação.

- P1. **`RegistroAjusteLoa` novo não salva com `save()` padrão.** `CmjSearchMixin.save()` chama
  `hook_emendaloa__search`, que lê o M2M `emendaloa` antes de existir `pk` e lança `ValueError`
  (`cmj/mixins.py:406-421`, `cmj/loa/models/m_ajusteloa.py:199-201`). O teste de LOA-FASE-061 contorna
  com `save(auto_update_search=False)`. Falta verificar se a tela de cadastro passa pelo mesmo erro.
- P2. **A incorporação que leva a fase a 20 (LOA-FASE-054) não tem teste.** O fluxo de
  `ConfirmarProposicaoForm` exige proposição e protocolo completos. Pelo mesmo motivo, o registro do
  usuário nessa transição (LOA-FASE-067) também não tem teste.

## Fora do escopo

Cálculo de valores por parlamentar, registros contábeis, ajustes, empenhos e assinatura de documentos,
exceto quando dependem diretamente da fase.
