# API: acesso às rotas geradas

Status: observado, com API-ACS-010, 011, 030, 031, 032, 034 a 037, 039, 041 a 045, 047, 049 e 050 implementadas e
API-ACS-018, 019, 033 e 048 acordadas (2026-11-21 e 22)
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `sapl/api/permissions.py`, `cmj/settings/drf.py`, `sapl/rules/map_rules.py`,
`cmj/globalrules/map_rules.py`, `sapl/api/urls.py`, `sapl/api/mixins.py`, `sapl/api/views_*.py`,
`cmj/api/views_*.py`, `cmj/api/loa/views/`, `sapl/compilacao/services/s_visibilidade.py`,
`cmj/search/services/s_chat.py`, `cmj/arq/services/s_draft.py`, `cmj/core/services/s_auditoria.py`,
`cmj/core/services/s_areatrabalho.py`, `cmj/painelset/signals_sync_refresh.py`
Testes: `sapl/api/tests/test_api_acesso.py`, `sapl/api/tests/test_api_esquema.py`,
`cmj/painelset/test_sync_refresh.py`,
`sapl/compilacao/tests/test_visibilidade.py`, `cmj/search/test_chat_service.py`,
`cmj/arq/test_draft_service.py`, `cmj/core/test_auditoria.py`

Quem alcança cada rota `/api/<app_label>/<model>/`, por qual método, e onde a visibilidade dos
registros é decidida.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste, e a `[acordado]` é convenção
confirmada pelo responsável. As marcadas com "(executado)" foram conferidas em 2026-11-21 no banco de
desenvolvimento, com a sessão do banco em somente leitura (`default_transaction_read_only=on`), de
três formas:

- **inventário**: `GET` anônimo com `django.test.Client` na lista e no detalhe das rotas geradas
  (217 na data; 215 desde API-ACS-039 e 041, com a lista conferida de novo em 2026-11-22);
- **sonda de permissão**: para cada rota, método e action, só a autenticação e as permissões do
  viewset (`initial`) e a busca do objeto (`get_object`), sem executar criação, alteração, exclusão
  nem o corpo das actions; como anônimo e como um usuário ativo sem grupo e sem permissão;
- **ponta a ponta**: requisição completa na rota real, quando indicado.

As demais vieram da leitura do código.

## Escopo

A classe de permissão padrão, o mapa de permissões públicas, a autenticação, a escrita pelos
viewsets gerados, as actions e os pontos em que um viewset restringe os registros. As regras de
negócio de cada viewset customizado entram só como inventário. O mecanismo de geração está em
[gerador.md](./gerador.md) (`API-GER`).

## Regras

### Permissão padrão

- API-ACS-001 [observado] A permissão padrão é `SaplModelPermissions`, e a autenticação aceita
  token e sessão. Evidência: `cmj/settings/drf.py:17-21`.
- API-ACS-002 [observado] `GET`, `HEAD` e `OPTIONS` exigem as duas permissões `list_<model>` e
  `detail_<model>`; `POST` exige `add_`, `PUT` e `PATCH` exigem `change_`, e `DELETE` exige
  `delete_`. Evidência: `sapl/api/permissions.py:12-29`.
- API-ACS-003 [observado] A permissão é só por model: não há checagem por objeto
  (`has_object_permission`). Quem tem a permissão do model alcança todos os registros que o
  queryset do viewset devolver. Evidência: `sapl/api/permissions.py:31-63`.
- API-ACS-004 [observado] Se todas as permissões exigidas pelo método estão no mapa de permissões
  públicas do model, a requisição passa sem autenticação. Evidência:
  `sapl/api/permissions.py:47-57`.
- API-ACS-005 [observado] O mapa público junta o terceiro elemento de cada regra de
  `sapl/rules/map_rules.py` e de `cmj/globalrules/map_rules.py`; o conjunto usado é
  `{list, detail}`. Evidência: `sapl/api/permissions.py:6-7`, `sapl/rules/map_rules.py:70`,
  `sapl/rules/map_rules.py:397-418`, `cmj/globalrules/map_rules.py:423-446`.
- API-ACS-006 [observado] Fora do mapa público, anônimo recebe 401 e autenticado sem a permissão
  recebe 403. Evidência: `sapl/api/permissions.py:59-63`.
- API-ACS-007 [observado] `has_permission` chama `view.get_queryset()` antes de decidir. Um
  `get_queryset` que filtre por `request.user` sem tratar o anônimo falha com erro 500, em vez de
  401. (executado) Hoje nenhuma lista de rota gerada falha assim. Evidência:
  `sapl/api/permissions.py:35-36`.

### O que anônimo lê

- API-ACS-008 [observado] (executado, inventário) Anônimo recebe 200 na lista de 140 das 215 rotas
  e 401 nas outras 75. Evidência: `sapl/api/permissions.py:51-57`.

| App | Rotas | Lista a anônimo | App | Rotas | Lista a anônimo |
| --- | --- | --- | --- | --- | --- |
| `agenda` | 3 | 0 | `materia` | 25 | 23 |
| `arq` | 4 | 0 | `norma` | 9 | 9 |
| `audiencia` | 3 | 3 | `painel` | 2 | 2 |
| `base` | 6 | 3 | `painelset` | 7 | 6 |
| `cerimonial` | 2 | 0 | `parlamentares` | 24 | 21 |
| `comissoes` | 8 | 8 | `protocoloadm` | 9 | 5 |
| `compilacao` | 15 | 10 | `search` | 3 | 0 |
| `contenttypes` | 1 | 1 | `sessao` | 22 | 22 |
| `core` | 17 | 0 | `sigad` | 13 | 0 |
| `diarios` | 3 | 2 | `videos` | 4 | 0 |
| `loa` | 35 | 25 | | | |

- API-ACS-009 [observado] (executado, sonda) Um usuário autenticado sem grupo e sem permissão lê
  exatamente as mesmas rotas que anônimo: nenhuma lista e nenhuma action passa para ele e não para
  anônimo. Evidência: `sapl/api/permissions.py:59-63`.
- API-ACS-010 [implementado] (executado) `contenttypes/contenttype` é público e só de leitura:
  lista os 304 models do sistema, com id, app e nome, inclusive os de apps sem rota na API. Fica
  público por decisão de 2026-11-22: a lista não traz dado, e os models instalados já estão no
  código, que é público. Evidência: `sapl/rules/map_rules.py:83`, `sapl/api/views_base.py:23-25`.
- API-ACS-011 [implementado] (executado) `GET /api/schema/` (OpenAPI), `/api/schema/swagger-ui/` e
  `/api/schema/redoc/` respondem a anônimo. O esquema é o mesmo para qualquer usuário e descreve
  as 215 rotas, inclusive as restritas, com campos e filtros; traz só estrutura, nenhum dado
  (conferido em 2026-11-22 no esquema gerado). Fica público por decisão de 2026-11-22: é a
  documentação da API de dados abertos, não revela nada além do código, que é público, e quem
  protege as rotas restritas é a permissão de cada uma. Evidência: `sapl/api/urls.py:24-36`,
  `cmj/settings/drf.py:48-52`.
- API-ACS-012 [retirada] Substituída por API-ACS-050.
- API-ACS-050 [implementado] Requisição anônima com o parâmetro `u` na URL é recusada com status
  444, sem corpo, antes de a view rodar, em qualquer rota do portal. O parâmetro era o carimbo de
  tempo que as telas acrescentavam às prévias de PDF; hoje nenhuma tela o envia, e a recusa fica
  para robôs que repetem URLs antigas com ele. Quem está autenticado por sessão é atendido.
  Evidência: `cmj/middleware/disabled.py:48-52`.
- API-ACS-032 [implementado] `parlamentares/dependente` e `parlamentares/votante` não são públicas
  na API: a leitura exige `list_` e `detail_` do model, como as telas desses models, que pedem
  login. Anônimo recebe 401 e autenticado sem a permissão recebe 403. O canal de sincronização
  por WebSocket lê o mesmo mapa: para anônimo, o aviso de alteração desses models segue sem o
  conteúdo do registro. Evidência: `sapl/rules/map_rules.py:309`, `sapl/rules/map_rules.py:316`,
  `cmj/core/consumers.py:62-82`.

### Permissões próprias de viewset

- API-ACS-013 [observado] (executado, inventário) 202 rotas usam `SaplModelPermissions` e 13 trocam
  a classe, conforme a tabela. Evidência: `sapl/api/views_materia.py:78-93`,
  `sapl/api/views_parlamentares.py:23-32`, `sapl/api/permissions.py:66-77`,
  `cmj/api/loa/views/loa.py:52-76`, `cmj/api/loa/views/emendaloa.py:25`.

| Rotas | Classe | O que muda |
| --- | --- | --- |
| `materia/proposicao` | `ProposicaoPermission` | `GET` sempre passa; o `get_queryset` filtra |
| `parlamentares/parlamentar` | `ParlamentarPermission` | `GET` sempre passa |
| 5 de `protocoloadm` | `ContainerPermission` | leitura sempre passa; rotas só de leitura (API-ACS-030, 031) |
| `loa/loa` | `LoaPermission` | detalhe e duas actions `POST` passam sem permissão |
| 5 de `loa` (emenda, agrupamento e registros) | `EmendaLoaPermission` e filhas | regras da LOA |

- API-ACS-014 [retirada] Substituída por API-ACS-030.
- API-ACS-015 [observado] O `get_queryset` de `ControlAccessFileForContainerMixin` devolve, para
  anônimo e para usuário sem área de trabalho, os registros de área de trabalho pública; para
  operador com as permissões exigidas, os das áreas em que opera. Evidência:
  `sapl/api/mixins.py:488-510`.
- API-ACS-016 [retirada] Substituída por API-ACS-031.
- API-ACS-017 [observado] (executado, sonda) Nenhum `POST`, `PUT`, `PATCH` ou `DELETE` padrão passa
  para anônimo nem para autenticado sem vínculo, em nenhuma das 215 rotas. Evidência:
  `sapl/api/permissions.py:59-63`.
- API-ACS-030 [implementado] `ContainerPermission` libera `GET`, `HEAD` e `OPTIONS` sem conferir
  permissão de model, e deixa a visibilidade dos registros para o `get_queryset` do viewset. Em
  qualquer outro método vale `SaplModelPermissions`: usuário autenticado com a permissão do model
  para o método. Evidência: `sapl/api/permissions.py:66-77`.
- API-ACS-031 [implementado] As cinco rotas de `protocoloadm` que usam `ContainerPermission` (tipo
  de documento, documento administrativo, documento acessório, tramitação e anexação) são só de
  leitura na API. `POST`, `PUT`, `PATCH` e `DELETE` respondem 401 a anônimo, 403 a autenticado sem
  a permissão do model e 405 a quem a tem; a leitura anônima continua respondendo 200. Evidência:
  `sapl/api/views_protocoloadm.py:30-120`, `drfautoapi/drfautoapi.py:263-264`.

### Escrita pelos viewsets gerados

- API-ACS-018 [acordado] Os métodos de escrita ficam abertos nas rotas geradas, menos em
  `contenttypes/contenttype` e nas cinco de `protocoloadm` que usam
  `BusinessRulesNotImplementedMixin` (API-ACS-031). Evidência: `drfautoapi/drfautoapi.py:263-273`,
  `sapl/api/views_base.py:25`.
- API-ACS-019 [acordado] Quem tem `add_`, `change_` ou `delete_` de um model grava pela rota
  gerada com o que o serializer gerado validar; os forms das telas e as regras que eles aplicam
  não participam. Mantido por decisão de 2026-11-22: a regra de negócio de cada model passa a ser
  concentrada em classes de serviço, chamadas do mesmo jeito pela API, pelos forms e pelas views,
  e fechar a escrita pela API seria uma barreira provisória. Enquanto a regra de um model não
  estiver num serviço, a gravação dele pela API não passa pelas validações do form da tela.
  Evidência: `drfautoapi/drfautoapi.py:537-541`.
- API-ACS-020 [retirada] Substituída por API-ACS-039.
- API-ACS-039 [implementado] O model de usuário não tem rota na API: o app `core` é registrado sem
  ele, e `core/user` responde 404 a qualquer usuário, em qualquer método. Contas, senhas, grupos e
  permissões são administrados só pelas telas de usuário (`/sistema/usuario`). Nos demais models, a
  relação com usuário continua saindo como id, sem `expand` (API-SER-008). Evidência:
  `cmj/api/views_core.py:19-30`, `cmj/core/views_auth.py:100-116`.
- API-ACS-040 [retirada] Substituída por API-ACS-041 e API-ACS-042.
- API-ACS-041 [implementado] O registro de auditoria (`AuditLog`) não tem rota na API: o app `core`
  é registrado sem ele, e `core/auditlog` responde 404 a qualquer usuário, em qualquer método. A
  auditoria é consultada só pela tela de pesquisa, que exige `base.list_appconfig`. Em
  `sigad/midia`, a relação com o registro de auditoria sai como id, sem `expand`. Evidência:
  `cmj/api/views_core.py:19-30`, `cmj/core/views.py:1046-1051`.
- API-ACS-042 [implementado] O registro de auditoria guarda o objeto serializado por inteiro, menos
  o campo `password`, que não é gravado para model nenhum. Os registros gravados antes dessa regra
  são limpos pelo command `auditlog_limpa_credenciais`, que retira só esse campo e mantém os
  demais; com `--dry-run`, ele só conta. (executado) Na base local, 15 registros de auditoria de
  usuário ainda têm o campo e são os que o command alcança. Evidência:
  `cmj/core/services/s_auditoria.py:13-42`, `cmj/core/signals_functions.py:87-89`,
  `cmj/core/management/commands/auditlog_limpa_credenciais.py:20-29`.

### Actions

- API-ACS-021 [observado] Uma `@action` sem `permission_classes` herda a permissão do viewset e é
  julgada pelo método HTTP: action `GET` de model público é pública. Evidência:
  `sapl/api/permissions.py:45`.
- API-ACS-022 [observado] (executado, sonda) Das 49 actions com método de escrita, anônimo passa em
  duas: `loa/loa/<pk>/despesas_agrupadas` e `loa/loa/<pk>/espelho` (`POST`), que só consultam, e
  só em LOA publicada (API-ACS-045). As demais negam o acesso a anônimo e ao autenticado sem
  vínculo. Evidência: `cmj/api/loa/views/loa.py:61-73`.
- API-ACS-045 [implementado] As consultas `despesas_agrupadas` e `espelho` de `loa/loa` seguem a
  publicação da LOA, como o detalhe: em LOA não publicada, anônimo recebe 401; em LOA publicada,
  qualquer um consulta. Evidência: `cmj/api/loa/views/loa.py:61-73`.
- API-ACS-023 [retirada] Substituída por API-ACS-049.
- API-ACS-049 [implementado] `materia/tipoproposicao/tipos_do_autor_contectado/` devolve os tipos
  de proposição do tipo do autor que o usuário opera. Anônimo recebe 401; usuário autenticado que
  não opera nenhum autor recebe a lista vazia. Evidência: `sapl/api/views_materia.py:32-48`.

### Visibilidade dos registros

- API-ACS-024 [observado] (executado, inventário) Sem `get_queryset` próprio, o viewset gerado
  devolve `Model.objects.all()`. Dezenove viewsets têm `get_queryset` próprio, conforme a tabela.
  Evidência: `drfautoapi/drfautoapi.py:539`.

| Rota | Restrição | Evidência |
| --- | --- | --- |
| `materia/proposicao` | anônimo vê só as recebidas; autor vê as suas | `sapl/api/views_materia.py:95-115` |
| 5 de `compilacao` | visibilidade do texto articulado e da nota (API-ACS-034, 035) | `sapl/api/views_compilacao.py:22-58` |
| 5 de `protocoloadm` | área de trabalho pública ou do operador | `sapl/api/mixins.py:488-510` |
| `loa/emendaloa` | leitura segue a visibilidade da listagem | `cmj/api/loa/views/emendaloa.py:61-67` |
| `loa/subfuncao` | filtro opcional, sem efeito de visibilidade | `cmj/api/loa/views/subfuncao.py:3-11` |
| `arq/draft` e `arq/draftmidia` | só os do usuário (API-ACS-037) | `cmj/api/views_arq.py:49-51`, `cmj/api/views_arq.py:399-401` |
| `search/chatsession` e `search/chatmessage` | só os do usuário (API-ACS-036) | `cmj/api/views_search.py:18-32` |
| `agenda/evento` e `protocoloadm/statustramitacaoadministrativo` | só os das áreas em que o usuário opera (API-ACS-044) | `cmj/api/views_agenda.py:19-21`, `sapl/api/views_protocoloadm.py:123-125` |

- API-ACS-025 [retirada] Substituída por API-ACS-034.
- API-ACS-026 [retirada] Substituída por API-ACS-035.
- API-ACS-027 [retirada] Substituída por API-ACS-036.
- API-ACS-028 [retirada] Substituída por API-ACS-037.
- API-ACS-029 [retirada] Substituída por API-ACS-043.
- API-ACS-043 [implementado] Na área de trabalho pública, todo documento administrativo é público na
  API, como nas telas, qualquer que seja o campo `visibilidade`: anônimo lista o documento e
  recebe o arquivo. A marca só vale para o link de compartilhamento dos documentos das áreas
  restritas, e é conferida quando a requisição traz o código. (executado) Na base local, a área
  pública tem 6.394 documentos, 2.594 deles "Privado": 2.490 são de 2020 ou antes e têm a marca por
  ser o valor padrão de quando o campo foi criado, e 104 são posteriores. Evidência:
  `sapl/api/views_protocoloadm.py:45-87`, `sapl/api/mixins.py:488-510`,
  `sapl/protocoloadm/models.py:329-338`.

- API-ACS-033 [acordado] A visibilidade dos registros de um model na API fica no `get_queryset`
  do seu viewset, e a regra de negócio fica numa classe de serviço do app do model, que recebe o
  usuário e o queryset. É esse o ponto que o `expand` e as actions de arquivo consultam. Evidência:
  `drfautoapi/drfautoapi.py:946-961`, `sapl/api/mixins.py:290`,
  `sapl/compilacao/services/s_visibilidade.py:15-22`.
- API-ACS-034 [implementado] Um texto articulado só é consultado por quem o vê nas telas: texto
  "Público" ou "Imutável Público", por todos; os demais, pelo dono ou por quem tem a permissão do
  estado (`view_restricted_textoarticulado` para "Imutável Restrito" e
  `change_dispositivo_edicao_dinamica` para "Em Edição"); o "Privado", só pelo dono, nem pelo
  superusuário. `compilacao/dispositivo` e `compilacao/publicacao` seguem o texto a que pertencem,
  e `compilacao/vide` segue o texto do dispositivo de origem. Evidência:
  `sapl/compilacao/services/s_visibilidade.py:24-58`, `sapl/api/views_compilacao.py:22-51`.
- API-ACS-035 [implementado] Uma nota só é consultada se o texto do seu dispositivo for visível
  (API-ACS-034) e conforme a publicidade: "Nota Pública" por todos, "Nota Institucional" por quem
  está autenticado e "Nota Privada" pelo dono; superusuário consulta todas. Evidência:
  `sapl/compilacao/services/s_visibilidade.py:60-71`, `sapl/api/views_compilacao.py:54-58`.

- API-ACS-036 [implementado] Em `search/chatsession` e `search/chatmessage`, cada usuário alcança
  só as próprias sessões e as mensagens delas, qualquer que seja a permissão de model que tenha,
  inclusive superusuário; anônimo recebe 401. Uma mensagem só é criada ou movida para uma sessão do
  próprio usuário; para a de outro, a resposta é 403. Evidência:
  `cmj/search/services/s_chat.py:1-23`, `cmj/api/views_search.py:15-47`.
- API-ACS-037 [implementado] Em `arq/draft` e `arq/draftmidia`, cada usuário alcança só os próprios
  drafts e as mídias deles, inclusive nas actions de arquivo e de conversão da mídia; anônimo
  recebe 401. Uma mídia só é criada ou movida para um draft do próprio usuário; para o de outro, a
  resposta é 403. Evidência: `cmj/arq/services/s_draft.py:1-23`, `cmj/api/views_arq.py:49-51`,
  `cmj/api/views_arq.py:399-414`.
- API-ACS-038 [retirada] Substituída por API-ACS-044 e API-ACS-046.
- API-ACS-044 [implementado] Em `agenda/evento` e `protocoloadm/statustramitacaoadministrativo`, o
  usuário com a permissão do model alcança só os registros das áreas de trabalho em que opera,
  como nas telas desses models, inclusive o superusuário; quem não opera nenhuma área recebe a
  lista vazia, e o registro de outra área responde 404 na leitura, na alteração e na exclusão.
  Criar um registro em área em que não opera, ou mover um registro para ela, responde 403. A regra
  fica em `AreaTrabalhoService`, no app do model de área de trabalho, por valer para models de
  apps diferentes. (executado) Na base local os 498 eventos são da área pública e os 6 status se
  dividem entre a área pública e um setor administrativo. Evidência:
  `cmj/core/services/s_areatrabalho.py:4-26`, `sapl/api/mixins.py:513-541`,
  `cmj/api/views_agenda.py:19-21`, `sapl/api/views_protocoloadm.py:123-125`,
  `cmj/agenda/views.py:15-19`, `sapl/protocoloadm/views.py:195-198`.
- API-ACS-046 [observado] `cerimonial/visita` não pertence a uma área de trabalho: o model guarda
  só os setores visitados, e a tela de visitas também não filtra por área. Quem tem a permissão do
  model lê todas as visitas, na tela e na API. Evidência: `cmj/cerimonial/models.py:1153-1174`,
  `cmj/cerimonial/views.py:78-86`, `cmj/api/views_cerimonial.py:16-22`.
- API-ACS-047 [implementado] O canal de sincronização por WebSocket (`/ws/sync/`) avisa a todos os
  clientes conectados cada gravação e exclusão dos models dos apps `painelset`, `sessao`,
  `parlamentares`, `materia`, `base` e `norma`, com app, model, id e hora. O registro vai junto
  só quando o viewset do model não restringe por registro, e o consumer o retira de quem não tem a
  permissão de detalhe do model (API-ACS-032). Quando o viewset restringe por registro
  (`get_queryset` próprio ou queryset filtrado, o critério de API-SER-026), o aviso vai sem o
  registro para todos, inclusive superusuário: quem pode vê-lo busca pela API, que aplica a
  visibilidade (API-ACS-033). (executado) Dos 93 models desses apps, só `materia/proposicao` está
  nessa condição; o v6 e o v8 já buscam pela API quando o aviso chega sem o registro. Evidência:
  `cmj/painelset/signals_sync_refresh.py:14-33`, `cmj/painelset/signals_sync_refresh.py:66-78`,
  `drfautoapi/drfautoapi.py:319-325`, `cmj/painelset/consumers.py:165-199`,
  `_frontend/v6/src/stores/SyncStore.js:213-235`.
- API-ACS-048 [acordado] O nginx do container responde em `/api` com
  `Access-Control-Allow-Origin: *`, sem `Access-Control-Allow-Credentials`: a API é legível por
  script de qualquer origem, sem os cookies do visitante. O cabeçalho `Authorization` está entre
  os liberados, e por isso a autenticação por token funciona entre origens; os frontends do
  portal chamam a API na mesma origem e não passam por essa conferência. Decisão de 2026-11-22.
  Evidência: `docker/nginx/cmj_docker.conf:155-169`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1 a 7 de `docs/specs/README.md`, sobre as permissões e a
visibilidade das rotas geradas. Não é auditoria de cada viewset customizado.

Nenhum risco encontrado nos itens 1 a 7 (2026-11-22).

Itens sem achado nesta spec: 4 (nenhuma execução no servidor nas permissões). Os itens 2, 3 e 7
estão em [serializacao.md](./serializacao.md), [arquivos.md](./arquivos.md) e
[paginacao-custo.md](./paginacao-custo.md).

## Dúvidas

Nenhuma dúvida em aberto.

## Fora do escopo

- Regras de negócio dos viewsets da LOA, do `painelset`, do `arq` e de `DocumentoViewSet`.
- A visibilidade por `publicado` nas rotas da LOA (LOA, ajustes, prestação de contas): é a dúvida
  D2 do painel de prestação de contas, a resolver com a convenção de API-ACS-033.
- Login e token (`docs/specs/api/login.md`); `recria_token` exige `IsAdminUser`
  (`sapl/api/views.py:22-24`) e não foi analisado além disso.
- Campos devolvidos e `expand`: [serializacao.md](./serializacao.md). Filtros:
  [filtros.md](./filtros.md). Arquivos: [arquivos.md](./arquivos.md).
