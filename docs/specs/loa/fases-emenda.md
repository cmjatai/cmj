# LOA: fases da emenda

Status: acordado, implementação pendente
Última verificação: 2026-11-19 (commit `9b96527d8`)
Código principal: `cmj/loa/models/m_emendaloa.py`, `cmj/loa/views/v_emendaloa.py`,
`cmj/loa/forms/f_emendaloa.py`, `cmj/loa/models/m_agrupamento.py`, `cmj/api/loa/views/`
Testes: nenhum encontrado para `EmendaLoa`

As regras `[observado]` descrevem o comportamento atual, obtido por leitura do código, sem executar
os fluxos. As regras de negócio confirmadas em 2026-11-19 estão em "Regras acordadas": `[acordado]`
indica que o código já atende e `[desejado]` indica que ele ainda precisa mudar. Quando uma regra
`[observado]` conflitar com uma delas, vale a regra acordada.

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

- LOA-FASE-050 [desejado] O servidor aplica toda regra de fase. Controles do JavaScript ou da tela só
  orientam o usuário, e uma requisição que tente contorná-los deve ser negada.

### Quem muda cada fase

- LOA-FASE-051 [desejado] O autor só cria emenda na fase 10. Hoje: o formulário atende
  (`cmj/loa/forms/f_emendaloa.py:480-482`), mas o POST da API não valida a fase
  (`cmj/api/loa/views/emendaloa.py:47-55`).
- LOA-FASE-052 [desejado] O autor pode mudar manualmente de 10 para 12 na edição e voltar de 12 para
  10 enquanto o editor contábil não capturar a emenda (12 → 15). Hoje: o PATCH aceita qualquer fase válida (`cmj/api/loa/views/emendaloa.py:57-81`).
- LOA-FASE-053 [desejado] O editor contábil (`emendaloa_full_editor`, sem ser superusuário) faz as
  transições 12 → 15, 12 → 17, 15 → 17 e 17 → 15. O Operador da LOA segue LOA-FASE-065. Hoje:
  formulário e botões não verificam a fase de origem (`cmj/loa/forms/f_emendaloa.py:472-513`,
  `cmj/loa/views/v_emendaloa.py:1098-1108`).
- LOA-FASE-054 [desejado] O sistema muda para 20 ao incorporar a proposição associada à emenda na
  matéria. Manualmente, só superusuário e Operador da LOA podem escolher essa fase. Hoje: a incorporação
  e o select atendem (`sapl/materia/forms.py:3418-3422`), mas o PATCH aceita 20 de outros usuários.
- LOA-FASE-055 [desejado] Emenda já na fase 20 ou superior só é movimentada por superusuário ou
  Operador da LOA. Hoje: a tela atende, pois bloqueia os demais ao abrir a edição acima de 17
  (`cmj/loa/views/v_emendaloa.py:1124-1132`), mas o POST e o PATCH não fazem essa verificação.
- LOA-FASE-062 [acordado] O superusuário usa a mesma tela de edição do autor, sem limitação das fases
  no select. Evidência: `cmj/loa/forms/f_emendaloa.py:472-513`, `cmj/loa/views/v_emendaloa.py:1082-1096`.
- LOA-FASE-063 [desejado] O editor contábil pode devolver para a fase 10, pelo botão "Devolver para
  correção", emendas nas fases 15 ou 17. Hoje: o botão funciona, mas o POST não verifica a fase de
  origem (`cmj/loa/views/v_emendaloa.py:1098-1108`).
- LOA-FASE-065 [acordado] O Operador da LOA acessa e edita a emenda em qualquer fase, vê todas as
  fases no select e pode fazer as transições disponíveis nele. O acesso é identificado pelas permissões
  `add_emendaloa`, `change_emendaloa` e `emendaloa_full_editor`. A fase -10 continua oculta pelo manager
  padrão (LOA-FASE-002). Evidência: `cmj/loa/views/v_emendaloa.py:1071-1081`,
  `cmj/loa/forms/f_emendaloa.py:472-513`, `cmj/globalrules/map_rules.py:241-250`.
- LOA-FASE-066 [desejado] A captura automática de 12 para 15 ao abrir a edição vale só para o editor
  contábil. O superusuário abre a emenda sem mudar a fase e só a altera manualmente no formulário. Hoje:
  a captura também ocorre para o superusuário (`cmj/loa/views/v_emendaloa.py:1115-1121`).

### Emenda coletiva

- LOA-FASE-056 [acordado] Ao gerar a coletiva, a emenda de origem passa para -10. Ao cancelar, volta
  para 15. Evidência: `cmj/loa/models/m_agrupamento.py:268-276`, `cmj/loa/models/m_agrupamento.py:315-318`.
- LOA-FASE-057 [desejado] O cancelamento não altera a fase das emendas do agrupamento que não estavam
  em -10. Hoje: todas as visíveis vão para 15 (`cmj/api/loa/views/agrupamento.py:111-113`).
- LOA-FASE-064 [desejado] A emenda coletiva recebe como dono o `owner` da primeira emenda do conjunto,
  `emenda["emendas"][0].owner_id`; a lista segue a ordem por `id`. Hoje: usa `owner_id = 1`
  (`cmj/loa/models/m_agrupamento.py:299-301`), o que a deixa fora dos filtros de proposição por autor
  (`cmj/loa/tasks.py:22-29`, `sapl/materia/forms.py:3278-3296`).

### Inclusão em agrupamento

- LOA-FASE-058 [desejado] O servidor nega a inclusão de emenda na fase 10. Hoje: só o JavaScript
  impede (`_frontend/v2018/src/__apps/loa/agrupamento/AgrupamentoUpdate.js:361`), e a API não valida
  (`cmj/api/loa/views/agrupamentoemendaloa.py:64-72`).
- LOA-FASE-059 [desejado] O servidor aceita apenas emendas que a tela permite incluir: fase 12 ou 15 e
  mesmo ano da LOA do agrupamento. Hoje: esses filtros existem só na busca
  (`cmj/api/loa/views/emendaloa.py:341`).
- LOA-FASE-060 [desejado] O servidor define a fase resultante da inclusão (15) e ignora
  `emendaloa__fase` enviado pelo cliente. Hoje: o valor é gravado sem validação
  (`cmj/api/loa/views/agrupamentoemendaloa.py:68-72`).

### Histórico

- LOA-FASE-067 [desejado] Implementação futura: `EmendaLoaHistoricoFase` registra, por FK, o usuário
  que mudou a fase. A FK precisa aceitar vazio para os registros antigos e para mudanças sem usuário, e
  o signal precisará receber o usuário, que ele não conhece hoje (`cmj/loa/models/m_emendaloa.py:945-963`,
  `cmj/loa/signals.py:18-30`).

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
  `EmendaLoaHistoricoFase`, com fase e horário, sem o usuário. Evidência: `cmj/loa/signals.py:18-30`,
  `cmj/loa/models/m_emendaloa.py:945-963`.

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

### Efeitos em outros fluxos

- LOA-FASE-040 [observado] Registro contábil da emenda só pode ser alterado na fase 15, por
  `emendaloa_full_editor`. Evidência: `cmj/api/loa/views/emendaloaregistrocontabil.py:290-306`.
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

Devem ser decididas antes de implementar as regras afetadas. Não bloqueiam os demais testes.

- D13. **Botões em fases avançadas.** Com o acesso do Operador da LOA em qualquer fase (LOA-FASE-065),
  "Concluir edição" e "Devolver para correção" podem levar uma emenda de fase avançada para 17 ou 10
  (`cmj/loa/views/v_emendaloa.py:1098-1108`). Os botões devem ficar restritos às fases 15 e 17?
- D14. **Registros contábeis fora da fase 15.** O Operador da LOA edita a emenda em qualquer fase, mas
  a API só aceita alterar esses registros na fase 15 (LOA-FASE-040). Isso deve continuar assim?

## Fora do escopo

Cálculo de valores por parlamentar, registros contábeis, ajustes, empenhos e assinatura de documentos,
exceto quando dependem diretamente da fase.
