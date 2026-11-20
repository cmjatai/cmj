# LOA: edição da emenda

Status: observado; D3, D4 e D7 implementadas (LOA-EMD-070 a 079)
Última verificação: 2026-11-20 (commit `7c7c5f1c2`)
Código principal: `cmj/loa/views/v_emendaloa.py`, `cmj/loa/forms/f_emendaloa.py`,
`cmj/loa/services/s_emendaloa.py`, `cmj/api/loa/views/emendaloa.py`, `cmj/loa/models/m_emendaloa.py`,
`_frontend/v2018/src/__apps/loa/emenda/`
Testes: `cmj/loa/tests/test_edicao_emenda.py` (regras acordadas). As regras de fase citadas têm
testes em `cmj/loa/tests/test_fases_emenda.py`.

As regras `[observado]` foram obtidas por leitura do código, sem executar os fluxos. As decisões
tomadas sobre as dúvidas estão em "Regras acordadas": `[desejado]` indica que o código ainda precisa
mudar e `[implementado]` indica uma regra `[desejado]` já corrigida e coberta por teste. Quando uma
regra `[observado]` conflitar com uma delas, vale a regra acordada.

## Escopo

As telas de criação e edição de `EmendaLoa` (`/loa/emendaloa/...`) e o que acontece por trás delas:
- a view;
- o formulário;
- os endpoints da API chamados pela tela;
- o efeito do `save()` do model;
- o comportamento observável do frontend v2018, com o autosave em detalhe.

As regras de fase, de permissão por fase, de inclusão em agrupamento e de coletiva ficam em
`docs/specs/loa/fases-emenda.md`; esta spec só cita os IDs `LOA-FASE`.

### Perfis

Os mesmos de `fases-emenda.md`:
- **Autor:** operador de autor, sem permissões de LOA.
- **Editor contábil:** só `emendaloa_full_editor`.
- **Operador da LOA:** `add_emendaloa`, `change_emendaloa` e `emendaloa_full_editor`.
- **Superusuário.**

No formulário, `full_editor` vale para quem tem `emendaloa_full_editor` e não é superusuário, ou seja,
para o editor contábil **e** para o Operador da LOA (`cmj/loa/forms/f_emendaloa.py:271-274`).

## Regras acordadas

### Campos que cada perfil altera (D4, decidida em 2026-11-20)

A decisão de quais campos o usuário pode alterar fica em `EmendaLoaService`
(`cmj/loa/services/s_emendaloa.py`). A API e o formulário consultam o service.

- LOA-EMD-070 [implementado] O servidor só aceita alteração dos campos do model que o perfil do usuário
  pode alterar naquela emenda:
  - **Base, para todos os perfis abaixo:** `permite_juncao_coletiva`, `prefixo_indicacao`,
    `prefixo_finalidade`, `finalidade` e `bairro`.
  - **Autor** (operador de autor) com a emenda até a fase 12: base mais `tipo`, `fase`, `unidade` e
    `entidade`.
  - **Autor** com a emenda acima da fase 12: só a base.
  - **Autor**, em qualquer fase, quando a emenda resultante é modificativa (tipo 0): também `valor`,
    porque o formulário exige o Valor Global da modificativa (LOA-EMD-022).
  - **Editor contábil** (`emendaloa_full_editor`): base mais `tipo`, `fase`, `unidade` e `entidade`.
  - **Operador da LOA e superusuário** (`add_emendaloa`): base mais `tipo`, `fase`, `unidade`,
    `entidade`, `valor` e `materia`.

  Quem tem mais de um perfil soma as listas. A fase continua sujeita às transições de LOA-FASE-052,
  LOA-FASE-053 e LOA-FASE-065. Evidência: `EmendaLoaService.campos_alteraveis`
  (`cmj/loa/services/s_emendaloa.py:10-53`).
- LOA-EMD-071 [implementado] Nenhum perfil, nem o superusuário, altera pela API ou pelo formulário campos
  do model fora de LOA-EMD-070, como `owner`, `loa`, `metadata`, `indicacao`, `proposicao`,
  `emenda_coletiva` e `agrupamento_de_origem`. Esses campos continuam sendo mantidos pelos fluxos
  próprios: criação, coletiva, proposição, pré-visualização e `save()`. Evidência:
  `cmj/loa/services/s_emendaloa.py:82-104`.
- LOA-EMD-072 [implementado] Só conta como alteração o campo cujo valor enviado difere do valor gravado.
  Enviar um campo com o mesmo valor não é recusado. Evidência: `EmendaLoaService.campos_alterados`
  (`cmj/loa/services/s_emendaloa.py:54-80`).
- LOA-EMD-073 [implementado] O PATCH com um campo que o usuário não pode alterar é recusado com 400, sem
  gravar nada, e a mensagem cita o campo. Chaves que não são campos do model, como `busca_despesa`,
  continuam sendo ignoradas. Evidência: `cmj/api/loa/views/emendaloa.py:116-126`.
- LOA-EMD-074 [implementado] A action `updatevaloremenda` segue LOA-EMD-070 para o campo `valor`. Evidência:
  `cmj/api/loa/views/emendaloa.py:188-192`. Substitui LOA-EMD-028 quanto à permissão.
- LOA-EMD-075 [implementado] O POST do formulário de edição segue LOA-EMD-070. Campo alterado fora da lista,
  inclusive pelos campos ocultos de matéria, invalida o formulário. A criação não passa por essa
  regra: ela segue LOA-FASE-051. `indicacao` fica fora da verificação do formulário porque não é
  exibida e o `save()` a deriva da unidade (LOA-EMD-030). Evidência:
  `cmj/loa/forms/f_emendaloa.py:262-274`, `cmj/loa/forms/f_emendaloa.py:609-618`.

### Autoria, coautores e parlamentares (D3 e D7, decididas em 2026-11-20)

- LOA-EMD-076 [implementado] Edita a emenda, como autor, só o operador do mesmo autor do dono
  (`owner`). Operadores dos demais parlamentares participantes (coautores) não editam nada: a tela de
  edição, o PATCH e as actions da API os recusam, e eles só veem a emenda na listagem e no detalhe.
  Dono sem autor não tem operador de autor que o represente. Editor contábil, Operador da LOA e
  superusuário seguem LOA-EMD-003 e as regras de fase. Substitui o "operador de autor participante"
  de LOA-FASE-033 e resolve D7: o trecho morto foi removido. Corrige também a comparação anterior em
  que o dono sem autor (`None`) era igual a qualquer usuário sem autor, o que abria a edição para
  qualquer usuário logado. Evidência: `EmendaLoaService.e_autor_da_emenda`
  (`cmj/loa/services/s_emendaloa.py:108-127`), `cmj/api/loa/views/emendaloa.py:57-70`,
  `cmj/loa/views/v_emendaloa.py:99-101`, `cmj/loa/views/v_emendaloa.py:1123-1130`,
  `cmj/loa/views/v_emendaloa.py:1155-1159`.
- LOA-EMD-077 [implementado] Alteram valores por parlamentar e assinantes só o autor do dono, o
  Operador da LOA e o superusuário. O editor contábil não altera, como já acontecia no formulário. O
  autor do dono pode definir o valor dos coautores. Evidência:
  `EmendaLoaService.pode_alterar_parlamentares` (`cmj/loa/services/s_emendaloa.py:143-147`).
- LOA-EMD-078 [implementado] O parlamentar informado em `updatevalorparlamentar`,
  `update_parlassinantes` e no formulário precisa ser da LOA. Antes, a primeira action aceitava
  qualquer parlamentar, e a segunda dava erro 500. Evidência: `cmj/loa/services/s_emendaloa.py:149-178`.
- LOA-EMD-079 [implementado] O parlamentar do autor do dono não pode ter o valor zerado nem ser
  desmarcado como assinante, por nenhum perfil. Na criação, vale o parlamentar do autor de quem cria.
  Substitui a regra anterior, que só impedia o próprio operador de zerar o seu parlamentar
  (LOA-EMD-021, LOA-EMD-022, LOA-EMD-026 e LOA-EMD-027). Evidência:
  `EmendaLoaService.parlamentar_protegido` (`cmj/loa/services/s_emendaloa.py:129-141`),
  `cmj/api/loa/views/emendaloa.py:142-151`, `cmj/api/loa/views/emendaloa.py:225-234`,
  `cmj/loa/forms/f_emendaloa.py:582-607`.

## Regras observadas

### Acesso às telas

- LOA-EMD-001 [observado] A tela de criação aceita quem tem as permissões padrão de criação do CRUD e,
  sem elas, o operador de autor quando a LOA está publicada. Evidência:
  `cmj/loa/views/v_emendaloa.py:1023-1036`.
- LOA-EMD-002 [observado] O POST da API (`/api/loa/emendaloa/`) aceita quem tem `add_emendaloa`. Sem
  ela, aceita o operador de autor só quando a LOA **não** está publicada, a condição oposta à da tela
  (ver D1). Evidência: `cmj/api/loa/views/emendaloa.py:47-55`.
- LOA-EMD-003 [observado] A tela de edição aceita quem tem `emendaloa_full_editor`, o que inclui o
  superusuário e o Operador da LOA. Os demais só entram se forem operadores do mesmo autor do `owner`
  da emenda. Não é preciso participar da emenda: basta ser do mesmo autor. O trecho seguinte, que
  liberaria participantes de coletiva, nunca executa, porque fica depois do `return` (ver D7).
  Evidência: `cmj/loa/views/v_emendaloa.py:1176-1231`.
- LOA-EMD-004 [observado] Os bloqueios por fase ao abrir e ao enviar a edição seguem LOA-FASE-030,
  LOA-FASE-031, LOA-FASE-055 e LOA-FASE-065. A captura de 12 para 15 ao abrir segue LOA-FASE-011 e
  LOA-FASE-066. Evidência: `cmj/loa/views/v_emendaloa.py:1077-1174`.
- LOA-EMD-005 [observado] O PATCH da API, inclusive as actions `update_parlassinantes`,
  `updatevaloremenda` e `updatevalorparlamentar`, segue LOA-FASE-033:
  - com `change_emendaloa`, passa direto;
  - sem ela, exige emenda sem matéria e, além disso, `emendaloa_full_editor`, ou operador de autor
    participante com fase até 12 ou igual a 17.

  Evidência: `cmj/api/loa/views/emendaloa.py:29-83`.
- LOA-EMD-006 [observado] Os GET da API usados pela tela (`/view/` e `/totais/`) só exigem as
  permissões de listagem e detalhe, que são públicas para `EmendaLoa`. Evidência:
  `sapl/api/permissions.py:12-24`, `sapl/api/permissions.py:50-56`, `cmj/globalrules/map_rules.py:246-250`.

### Layout por perfil

- LOA-EMD-010 [observado] Sem `add_emendaloa`, os campos de matéria (tipo, número e ano) ficam ocultos
  e o campo `valor` (Valor Global) fica somente leitura. Com `add_emendaloa` (Operador da LOA e
  superusuário), os campos de matéria aparecem e o valor é editável. Evidência:
  `cmj/loa/forms/f_emendaloa.py:472-478`.
- LOA-EMD-011 [observado] Com `full_editor`, o formulário remove os campos de valor por parlamentar e
  de parlamentares assinantes, mostra o bloco "Registrar Deduções e Inserções" (busca de despesa e
  inclusão de registro contábil) e troca o botão Salvar por "CONCLUIR EDIÇÃO CONTÁBIL E FINALIZAR" e
  "DEVOLVER PARA CORREÇÃO". O efeito dos botões segue LOA-FASE-063 e LOA-FASE-069. Evidência:
  `cmj/loa/forms/f_emendaloa.py:314-316`, `cmj/loa/forms/f_emendaloa.py:325-376`,
  `cmj/loa/forms/f_emendaloa.py:413-433`, `cmj/loa/forms/f_emendaloa.py:515-518`,
  `cmj/loa/views/v_emendaloa.py:1093-1117`.
- LOA-EMD-012 [observado] O superusuário vê, ao mesmo tempo, o bloco de registros contábeis e os
  campos de parlamentares, com o botão Salvar padrão. Evidência:
  `cmj/loa/forms/f_emendaloa.py:325`, `cmj/loa/forms/f_emendaloa.py:431-433`.
- LOA-EMD-013 [observado] Na edição, os demais perfis veem a lista de registros contábeis só para
  leitura. A classe `btn-delete-d-none` esconde o botão de excluir apenas por CSS. Na criação, a lista
  não aparece. Evidência: `cmj/loa/forms/f_emendaloa.py:377-388`.
- LOA-EMD-014 [observado] Na edição, a tela reserva uma coluna para a pré-visualização do documento. A
  coluna ocupa 4 de 12 colunas com `full_editor` e 6 de 12 nos demais perfis. A criação não tem
  pré-visualização. Evidência: `cmj/loa/forms/f_emendaloa.py:393-407`.
- LOA-EMD-015 [observado] As opções de unidade são as unidades orçamentárias da LOA com
  `recebe_emenda_impositiva`. As de entidade são as entidades ativas. Evidência:
  `cmj/loa/forms/f_emendaloa.py:444-470`.
- LOA-EMD-016 [observado] Quando o usuário não tem `add_emendaloa` nem é `full_editor`, as opções de
  fase seguem LOA-FASE-010. Com fase maior que 12, `tipo`, `fase`, `unidade` e `entidade` ficam
  presos ao valor atual (LOA-FASE-032), e `indicacao` fica somente leitura. Os demais campos de texto
  continuam editáveis. Evidência: `cmj/loa/forms/f_emendaloa.py:480-509`.

### Valores e parlamentares

- LOA-EMD-020 [observado] O valor de cada parlamentar só é exibido para parlamentares da LOA. O campo
  fica somente leitura quando o usuário não tem `add_emendaloa` e `change_emendaloa` e é de outro
  autor, e o parlamentar ainda não está na emenda. Como a tela só admite operadores do mesmo autor
  (LOA-EMD-003), na prática o autor edita todos os valores. Evidência:
  `cmj/loa/forms/f_emendaloa.py:47-94`.
- LOA-EMD-021 [observado] No envio do formulário de emenda impositiva (tipo diferente de 0), o operador
  de autor que não é superusuário precisa informar o valor do próprio parlamentar. Evidência:
  `cmj/loa/forms/f_emendaloa.py:568-582`.
- LOA-EMD-022 [observado] No envio do formulário de emenda modificativa (tipo 0), o Valor Global
  precisa ser maior que zero, e o operador de autor que não é superusuário precisa marcar o próprio
  parlamentar entre os assinantes. Evidência: `cmj/loa/forms/f_emendaloa.py:583-605`.
- LOA-EMD-023 [observado] Ao salvar o formulário de emenda impositiva sem `full_editor`:
  - o Valor Global passa a ser a soma dos valores por parlamentar;
  - os vínculos `EmendaLoaParlamentar` são apagados e recriados só para os valores não nulos.

  Na modificativa, cada assinante é recriado com valor 1,00. Evidência:
  `cmj/loa/forms/f_emendaloa.py:621-662`.
- LOA-EMD-024 [observado] Na criação, o formulário define `owner` como o usuário e grava
  `metadata.style` com entrelinha 150 e espaço para assinaturas. Evidência:
  `cmj/loa/forms/f_emendaloa.py:617-619`.
- LOA-EMD-025 [observado] O envio do formulário vincula a matéria informada por tipo, número e ano. Se
  qualquer um dos três estiver vazio, a matéria é desvinculada. Sem `add_emendaloa`, os três campos
  vão ocultos com os valores atuais, o que preserva o vínculo. Evidência:
  `cmj/loa/forms/f_mixins.py:23-62`, `cmj/loa/views/v_emendaloa.py:1233-1242`.
- LOA-EMD-026 [observado] `update_parlassinantes` marca e desmarca o parlamentar na emenda. O operador
  de autor que não é superusuário não pode desmarcar o próprio parlamentar. Evidência:
  `cmj/api/loa/views/emendaloa.py:137-164`.
- LOA-EMD-027 [observado] `updatevalorparlamentar` cria ou altera o valor do parlamentar enviado e
  apaga o vínculo quando o valor é zero. O operador de autor que não é superusuário não pode zerar o
  valor do próprio parlamentar. O endpoint não confere se o parlamentar pertence à LOA nem se o
  usuário pode alterar o valor de outro parlamentar (ver D3). Um valor inválido vira 0,00. Evidência:
  `cmj/api/loa/views/emendaloa.py:203-246`.
- LOA-EMD-028 [observado] `updatevaloremenda` grava o Valor Global enviado sem aplicar a regra do
  campo somente leitura do formulário. Um valor inválido vira 0,01. Evidência:
  `cmj/api/loa/views/emendaloa.py:172-195`.

### Efeito do save() no model

- LOA-EMD-030 [observado] Todo `save()` copia a especificação da unidade para `indicacao` e, no fim,
  chama `loa.update_disponibilidades()`. Evidência: `cmj/loa/models/m_emendaloa.py:808-835`.
- LOA-EMD-031 [observado] Enquanto a LOA tem matéria e ainda não tem norma jurídica, o `save()` de uma
  emenda existente chama `sync()`, que tem estes efeitos:
  - **Emenda impositiva:**
    - o Valor Global passa a ser a soma dos valores por parlamentar;
    - se a emenda está em agrupamento, os registros contábeis dela são apagados e o agrupamento é
      sincronizado;
    - fora de agrupamento:
      - mudança de tipo ou unidade apaga os registros;
      - registros existentes são reescalados proporcionalmente ao novo valor;
      - sem registros, é criada uma dedução na despesa padrão da LOA, conforme a área da unidade.
  - **Emenda modificativa:** os registros são apagados e o Valor Global é dividido igualmente entre
    os parlamentares.

  Evidência: `cmj/loa/models/m_emendaloa.py:716-806`, `cmj/loa/models/m_emendaloa.py:816-823`.

### Frontend: criação

- LOA-EMD-040 [observado] Na criação, a tela alterna os campos conforme o tipo:
  - **Modificativa (tipo 0):** mostra os assinantes, oculta e desabilita os valores por parlamentar e
    libera o Valor Global.
  - **Demais tipos:** mostra os valores por parlamentar e deixa o Valor Global somente leitura.

  Não há autosave: tudo é gravado no envio. Depois de criar, a tela redireciona para a edição.
  Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaForm.js:7-48`,
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaCreate.js:1-12`,
  `cmj/loa/views/v_emendaloa.py:1013-1014`.
- LOA-EMD-041 [observado] Nas duas telas, preencher tipo, número e ano da matéria busca a ementa e a
  mostra abaixo dos campos. Evidência: `_templates/v2018/loa/recuperar_materia_script.html`,
  `_templates/v2018/loa/loa_form.html`.

### Frontend: edição e autosave

- LOA-EMD-050 [observado] Ao abrir a edição, a tela executa estes passos:
  1. carrega a emenda (`GET /api/loa/emendaloa/<pk>/`);
  2. aplica a alternância por tipo de LOA-EMD-040;
  3. monta a pré-visualização;
  4. carrega os totais (`/totais/`) e os registros contábeis
     (`/api/loa/emendaloaregistrocontabil/?emendaloa=<pk>&get_all=true`).

  Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:17-38`,
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:109-172`.
- LOA-EMD-051 [observado] A pré-visualização mostra a primeira página do documento como imagem, gerada
  por `GET /api/loa/emendaloa/<pk>/view/?page=1`. A imagem é um link para o PDF completo. Os controles
  "Entrelinha (%)" (100 a 350, passo 5) e "Incluir espaço para Assinaturas" refazem a imagem enviando
  `lineHeight` e `espacoAssinatura` na URL. Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:40-100`.
- LOA-EMD-052 [observado] O GET de `/view/` grava em `metadata.style` a entrelinha recebida, limitada a
  100–300 no servidor, e o espaço para assinaturas. Assim, uma requisição GET altera a emenda (ver D2).
  Evidência: `cmj/api/loa/views/emendaloa.py:264-299`.
- LOA-EMD-053 [observado] O autosave reage ao evento `change` de qualquer campo com `name` do
  formulário e envia **um campo por requisição**:

  | Campo alterado | Requisição |
  | --- | --- |
  | Valor de um parlamentar (input com `parlamentar_id`) | `PATCH /updatevalorparlamentar/` com `valor` e `parlamentar_id` |
  | Assinante (`parl_assinantes`) | `PATCH /update_parlassinantes/` com `parlamentar_id` e `checked` |
  | Valor Global (`valor`) | `PATCH /updatevaloremenda/` com `valor` |
  | Entrelinha ou espaço para assinaturas | Nenhuma: só refaz a pré-visualização (LOA-EMD-052) |
  | Qualquer outro campo | `PATCH /api/loa/emendaloa/<pk>/` com `{campo: valor}` |

  Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:356-408`.
- LOA-EMD-054 [observado] Pela última linha da tabela de LOA-EMD-053, campos que não são do model
  também geram PATCH: a busca de despesa, os campos `despesa_*`, `valor_despesa` e os de matéria. O
  serializer ignora esses campos, mas a emenda é salva mesmo assim, o que dispara os signals e, com a
  LOA em tramitação, o `sync()` de LOA-EMD-031 (ver D5). Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:386-388`,
  `cmj/api/loa/views/emendaloa.py:127-129`.
- LOA-EMD-055 [observado] Mudar a fase pelo autosave envia `PATCH` com `fase`, sujeito às transições de
  LOA-FASE-052, LOA-FASE-053 e LOA-FASE-065. Enquanto a fase escolhida é 10, o select fica marcado em
  vermelho. Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:347-354`,
  `cmj/api/loa/views/emendaloa.py:107-117`.
- LOA-EMD-056 [observado] O PATCH genérico usa o serializer com todos os campos do model e não aplica
  as restrições do formulário (LOA-EMD-010, LOA-EMD-016). Só a fase é conferida no servidor.
  Substituída por LOA-EMD-070 a 073.
  Evidência: `cmj/api/serializers.py:32-33`, `cmj/api/loa/serializers/__init__.py:105-136`,
  `cmj/api/loa/views/emendaloa.py:107-117`.
- LOA-EMD-057 [observado] Quando o autosave dá certo:
  - a tela atualiza a entrelinha e o Valor Global com os valores retornados;
  - recarrega os registros contábeis e a pré-visualização;
  - recarrega a página inteira se o campo alterado foi `tipo`.

  Quando falha, a tela recarrega a página sem mostrar a mensagem de erro do servidor, e a alteração
  rejeitada desaparece (ver D6). Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:393-407`.
- LOA-EMD-058 [observado] Enter não envia o formulário. No campo de busca de despesa, Enter seleciona o
  resultado quando há só um. Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:333-345`.
- LOA-EMD-059 [observado] O botão Salvar e os botões contábeis enviam o formulário inteiro por POST
  para a view de edição, que valida e grava pelas regras de LOA-EMD-021 a LOA-EMD-025, em adição ao que
  o autosave já gravou. Evidência: `cmj/loa/views/v_emendaloa.py:1077-1117`,
  `cmj/loa/forms/f_emendaloa.py:548-664`.

### Frontend: registros contábeis na edição

- LOA-EMD-060 [observado] A busca de despesa reage a cada tecla e consulta
  `/api/loa/despesaconsulta/search/?page_size=10&ano=<ano>&q=<texto>`.
  - Mostra até 10 resultados e destaca os termos com 3 ou mais letras.
  - Avisa quando há mais de 10 resultados ou nenhum.
  - Ao escolher um resultado, preenche os campos `despesa_*` e os deixa somente leitura.
  - Sem resultados, os campos ficam livres para preenchimento manual.

  Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:197-214`,
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:264-327`.
- LOA-EMD-061 [observado] O botão de incluir registro envia
  `POST /api/loa/emendaloaregistrocontabil/create_for_emendaloa_update/` com os dados da despesa, o
  `pk` da despesa escolhida (quando houver) e `valor_despesa`, que começa com o Valor Global da
  emenda. Os erros aparecem abaixo da busca, e os campos com problema ficam marcados. Evidência:
  `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:216-262`,
  `cmj/loa/forms/f_emendaloa.py:436-438`.
- LOA-EMD-062 [observado] Excluir um registro envia `DELETE /api/loa/emendaloaregistrocontabil/<pk>/`
  e atualiza a lista, os totais e a pré-visualização. A permissão para criar e excluir registros segue
  LOA-FASE-068. Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:174-195`,
  `cmj/api/loa/views/emendaloaregistrocontabil.py:287-299`.
- LOA-EMD-063 [observado] O rodapé dos registros mostra quatro totais. Os dois últimos ficam em azul
  quando são zero e em vermelho quando não são:
  - soma das inserções;
  - soma das deduções;
  - inserções + deduções;
  - Valor Global − inserções.

  Evidência: `_frontend/v2018/src/__apps/loa/emenda/EmendaLoaUpdate.js:113-138`,
  `cmj/loa/models/m_emendaloa.py:838-859`.

## Dúvidas

Ordenadas por risco. Em 2026-11-20, D4 virou LOA-EMD-070 a 075, e D3 e D7 viraram LOA-EMD-076 a 079.

- D8. **O autor edita a emenda na fase 17.** A tela e a API deixam o autor alterar valores,
  finalidade e parlamentares depois que a contabilidade liberou a emenda. Mudar valores na 17 desfaz o
  fechamento contábil, ou o reescala pelo `sync()` (LOA-EMD-031). A edição do autor na fase 17 é
  intencional? Se for, quais campos ele pode mudar?
- D1. **A criação pela tela e pela API exigem condições opostas.** Para o operador de autor, a tela de
  criação exige LOA publicada (LOA-EMD-001) e o POST da API exige LOA não publicada (LOA-EMD-002).
  Qual condição vale?
- D5. **O autosave grava a emenda sem mudança real.** Campos que não são do model geram PATCH e salvam a
  emenda (LOA-EMD-054). Com a LOA em tramitação, cada tecla na busca de despesa que gera `change`
  dispara o `sync()`, que pode apagar ou reescalar registros contábeis. O autosave deve ignorar esses
  campos?
- D6. **O erro do autosave some.** A falha recarrega a página sem mensagem (LOA-EMD-057). Uma transição
  de fase negada, por exemplo, só "volta" sem explicação. A tela deve mostrar o erro do servidor?
- D2. **O GET de `/view/` altera a emenda e é público.** O endpoint grava `metadata.style`
  (LOA-EMD-052), e o GET da API é público para `EmendaLoa` (LOA-EMD-006). Qualquer pessoa, mesmo
  anônima, pode mudar a entrelinha do documento de qualquer emenda visível, o que afeta o PDF da
  proposição. A gravação deve exigir permissão de edição, ou sair do GET?

## Pendências encontradas

Problemas vistos ao implementar as regras acordadas, fora delas.

- P1. **O PATCH genérico de `valor` sempre falha.** O `DecimalField` do serializer recusa "5000,00",
  e com "5000.00" o `validate_valor` recebe um `Decimal` e o trata como texto, o que também gera 400
  (`cmj/api/loa/serializers/__init__.py:172-200`). A tela não é afetada porque grava o Valor Global
  pela action `updatevaloremenda`. Por isso, a regra de `valor` é testada pelo service e pela action.

## Fora do escopo

- Regras de fase, permissões por fase, agrupamento e coletiva: `docs/specs/loa/fases-emenda.md`.
- Tela de detalhe, inclusive a geração da proposição: ver LOA-FASE-041.
- Listagem e filtros de emendas.
- Validação interna dos registros contábeis: serializer de `EmendaLoaRegistroContabil`.
- Conteúdo do PDF da emenda.
- `Loa.update_disponibilidades`.
- Ajustes técnicos, empenhos e prestação de contas.
