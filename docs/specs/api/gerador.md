# API: geração dos viewsets (`drfautoapi`)

Status: observado, com API-GER-031 a 037 e 040 a 043 implementadas e API-GER-038 acordada
(2026-11-22)
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `drfautoapi/drfautoapi.py`, `sapl/api/views.py`, `cmj/api/views.py`,
`sapl/api/urls.py`, `cmj/settings/drf.py`
Testes: `sapl/api/tests/test_api_condicional.py`, `sapl/api/tests/test_api_gerador.py`

Como as rotas `/api/<app_label>/<model>/` nascem: o registro dos models, o viewset que cada um
recebe, o mecanismo `@customize` e a resposta condicional (`Last-Modified`) aplicada a todos.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste, e a `[acordado]` é decisão confirmada
pelo responsável. As marcadas com "(executado)" foram conferidas em 2026-11-21 no banco de
desenvolvimento, com `django.test.Client` nas rotas reais e a sessão do banco em somente leitura
(`default_transaction_read_only=on`). As demais vieram da leitura do código.

Specs vizinhas: [acesso.md](./acesso.md) (`API-ACS`), [serializacao.md](./serializacao.md)
(`API-SER`), [filtros.md](./filtros.md) (`API-FIL`), [paginacao-custo.md](./paginacao-custo.md)
(`API-CUS`) e [arquivos.md](./arquivos.md) (`API-ARQ`).

## Escopo

`ApiViewSetConstrutor` (`build_class`, `router`, `import_modules`), `@customize`,
`wrapper_queryset_response_for_drf_action`, `DrfautoapiRouter`, a montagem de `/api/` em
`sapl/api/urls.py`, o `LastModifiedDecorator` e o `RespostaCondicionalMixin`. O que cada viewset customizado faz além disso
aparece só como inventário em [acesso.md](./acesso.md).

## Regras

### Registro dos models

- API-GER-001 [observado] `build_class` recebe uma lista de `AppConfig` ou de models. Para um app,
  gera um viewset para cada model de `app.get_models()`; para um model, só o dele. Evidência:
  `drfautoapi/drfautoapi.py:549-564`.
- API-GER-002 [observado] O registro é um único dicionário de classe, `_built_sets`, indexado por
  app e model. `SaplApiViewSetConstrutor` e `CmjApiViewSetConstrutor` são a mesma classe e, por
  isso, o mesmo registro. Evidência: `drfautoapi/drfautoapi.py:298`, `sapl/api/views.py:144`,
  `cmj/api/views.py:33`.
- API-GER-003 [observado] Só entra no registro o model cujo módulo é importado por
  `import_modules`: dez módulos `sapl.api.views_*` e dez de `cmj.api`. Cada módulo chama
  `build_class` ao ser importado. (executado) O resultado são 21 apps e 215 models. Evidência:
  `sapl/api/views.py:147-160`, `cmj/api/views.py:35-48`.
- API-GER-004 [observado] `contenttypes` entra junto com `base`, `cerimonial` entra só com
  `Visitante` e `Visita`, e `core` entra sem o model de usuário e sem o registro de auditoria
  (API-ACS-039, 041); os demais apps entram com todos os models. (executado) Apps instalados
  com models e fora da API: `ouvidoria`, `auth`, `admin`, `sessions`, `authtoken`, `social_django`,
  `easy_thumbnails`, `django_celery_results` e `django_celery_beat`. Evidência:
  `sapl/api/views_base.py:18-20`, `cmj/api/views_cerimonial.py:16-22`,
  `cmj/api/views_core.py:19-30`.

| App | Models | App | Models | App | Models |
| --- | --- | --- | --- | --- | --- |
| `agenda` | 3 | `core` | 17 | `painelset` | 7 |
| `arq` | 4 | `diarios` | 3 | `parlamentares` | 24 |
| `audiencia` | 3 | `loa` | 35 | `protocoloadm` | 9 |
| `base` | 6 | `materia` | 25 | `search` | 3 |
| `cerimonial` | 2 | `norma` | 9 | `sessao` | 22 |
| `comissoes` | 8 | `painel` | 2 | `sigad` | 13 |
| `compilacao` | 15 | `contenttypes` | 1 | `videos` | 4 |

### Rotas

- API-GER-005 [observado] `router()` registra cada viewset em `<app_label>/<model_name>`, com
  basename `<app_label>_<model_name>`. Evidência: `drfautoapi/drfautoapi.py:337-346`.
- API-GER-006 [retirada] Substituída por API-GER-043.
- API-GER-043 [implementado] `sapl/api/urls.py` monta um router só a partir do registro e inclui
  nele `documento` (`DocumentoViewSet`, escrito à mão). (executado) São 1.072 padrões para 536
  nomes, cada um registrado uma vez. Evidência: `sapl/api/urls.py:16-21`.
- API-GER-007 [observado] Lista e detalhe aceitam sufixo de formato (`.json`, `.c128.png`), com o
  padrão `[a-zA-Z.0-9]+`. Evidência: `drfautoapi/drfautoapi.py:290-291`.
- API-GER-008 [observado] (executado) `GET /api/` devolve a anônimo a raiz do router, com a lista de
  todas as rotas, inclusive `documento` (200, 15 kB). Evidência: `drfautoapi/drfautoapi.py:285-288`.

### Viewset gerado

- API-GER-009 [observado] O viewset gerado é um `ModelViewSet` completo (lista, detalhe, criação,
  alteração e exclusão), com `queryset = Model.objects.all()` e os serializer e filterset gerados.
  Evidência: `drfautoapi/drfautoapi.py:537-543`.
- API-GER-010 [observado] O único backend de filtro do viewset gerado é o `DjangoFilterBackend`. O
  `SearchFilter` declarado em `DEFAULT_FILTER_BACKENDS` não vale para ele. Evidência:
  `drfautoapi/drfautoapi.py:300-301`, `cmj/settings/drf.py:24-27`.
- API-GER-011 [observado] O serializer é procurado pelo nome `<Model>Serializer` nos módulos de
  `DEFAULT_SERIALIZER_MODULE` (`cmj.api.serializers` e `sapl.api.serializers`). Sem classe com esse
  nome, vale o `GLOBAL_SERIALIZER_MIXIN` (`CmjSerializerMixin`). A busca usa só o nome da classe do
  model, sem o app. Evidência: `drfautoapi/drfautoapi.py:429-446`,
  `drfautoapi/drfautoapi.py:478-481`, `cmj/settings/drf.py:41-46`.
- API-GER-012 [observado] O filterset segue a mesma busca, pelo nome `<Model>FilterSet` em
  `cmj.api.forms` e `sapl.api.forms`, com `CmjFilterSetMixin` como padrão. Evidência:
  `drfautoapi/drfautoapi.py:448-465`, `drfautoapi/drfautoapi.py:483-484`.
- API-GER-013 [observado] A classe gerada herda da encontrada e completa o `Meta`: põe o model se
  faltar, mantém `exclude` quando a base o declara e, sem `exclude` nem `fields`, usa `__all__`.
  Evidência: `drfautoapi/drfautoapi.py:501-518`, `drfautoapi/drfautoapi.py:526-532`.
- API-GER-014 [observado] O app `loa` chama `build_class` com `SERIALIZER_MODULE` próprio, que
  substitui os módulos padrão em vez de se somar a eles. Evidência:
  `cmj/api/loa/views/__init__.py:44-49`, `drfautoapi/drfautoapi.py:413-415`.
- API-GER-015 [observado] (executado) Cinco nomes de model se repetem entre apps registrados:
  `DocumentoAcessorio` (`materia`, `comissoes`), `Orgao` (`materia`, `loa`), `Painel` e `Cronometro`
  (`painel`, `painelset`) e `Evento` (`agenda`, `painelset`). Hoje nenhum deles tem serializer ou
  filterset achado por nome (API-GER-041). Evidência: `drfautoapi/drfautoapi.py:478-484`.
- API-GER-016 [retirada] Substituída por API-GER-040.
- API-GER-040 [implementado] Um módulo de serializers ou de filtersets configurado, ou um mixin
  global, que não importa interrompe a geração com erro de configuração, e o mesmo vale para o
  módulo que ainda está sendo importado quando `build_class` roda (importação circular): a API não
  sobe sem as classes próprias. Como as rotas são montadas com o URLconf, o `check` e o `migrate`
  falham com esse erro. (executado) Com a configuração atual nenhum módulo está nessa condição, e
  com um módulo inexistente o `migrate --check` termina com o erro. Evidência:
  `drfautoapi/drfautoapi.py:348-382`, `drfautoapi/drfautoapi.py:427-471`.
- API-GER-041 [implementado] A classe própria continua sendo achada pelo nome do model, sem o app.
  Se a classe achada declara em `Meta.model` um model diferente do que está sendo gerado, que é o
  caso de models de mesmo nome em apps diferentes, a geração é interrompida com erro de
  configuração que nomeia a classe e os dois models. Classe sem `Meta.model` vale para qualquer
  model com aquele nome. (executado) Dos serializers e filtersets com nome de model registrado, os
  16 e os 5 em uso servem ao model que declaram. Evidência: `drfautoapi/drfautoapi.py:383-393`,
  `drfautoapi/drfautoapi.py:486-491`.

### `@customize`

- API-GER-017 [observado] `@customize(Model)` cria uma classe que herda da classe decorada e do
  viewset já registrado para o model, e a põe no lugar dele no registro. Sem `build_class` anterior
  para o model, falha com `KeyError`. Evidência: `drfautoapi/drfautoapi.py:616-635`.
- API-GER-018 [observado] Se a classe decorada tem o método `build`, o que vai para o registro é o
  retorno dele. O viewset de autor usa isso para criar uma action por tipo de autor. Evidência:
  `drfautoapi/drfautoapi.py:629-630`, `sapl/api/views_base.py:71-93`.
- API-GER-019 [observado] (executado) 52 dos 215 viewsets passam por `@customize`; os outros 163
  são só o que o gerador produz. Evidência: `drfautoapi/drfautoapi.py:632-634`.
- API-GER-020 [observado] `wrapper_queryset_response_for_drf_action(model)` faz uma action devolver
  registros de outro model: troca o queryset, o serializer e o filterset da instância pelos
  atributos de classe do viewset desse model, aplica os filtros da requisição, pagina e serializa.
  O `get_queryset` e o `get_serializer` usados continuam sendo os do viewset que hospeda a action,
  não os do model devolvido. Evidência: `drfautoapi/drfautoapi.py:579-612`.
- API-GER-021 [retirada] Substituída por API-GER-042.
- API-GER-042 [implementado] `parlamentares/parlamentar/<pk>/proposicoes/` responde a qualquer
  usuário, inclusive anônimo, com as proposições do parlamentar enviadas, recebidas e não
  canceladas, que é o que a tela pública de proposições do parlamentar lista. O viewset de
  parlamentar não troca o serializer da resposta: os campos pessoais do parlamentar são retirados
  na classe do serializer (API-SER-027), em qualquer rota ou action. Os demais usos do decorator
  seguem como em API-GER-020. Evidência: `sapl/api/views_parlamentares.py:38-62`,
  `sapl/parlamentares/views.py:332-341`, `sapl/api/serializers.py:99-129`.

### Resposta condicional

- API-GER-022 [retirada] Substituída por API-GER-031.
- API-GER-023 [retirada] Substituída por API-GER-032.
- API-GER-024 [retirada] Substituída por API-GER-033.
- API-GER-025 [retirada] Substituída por API-GER-036.
- API-GER-026 [retirada] Substituída por API-GER-034 e API-GER-037.
- API-GER-027 [retirada] Substituída por API-GER-031.
- API-GER-028 [retirada] Substituída por API-GER-035.
- API-GER-029 [retirada] Substituída por API-GER-033.
- API-GER-030 [retirada] Substituída por API-GER-037.
- API-GER-031 [implementado] Todo viewset gerado recebe o `RespostaCondicionalMixin`. A resposta
  condicional vale só para a lista e o detalhe, em `GET` e `HEAD`, e só depois da autenticação, da
  permissão e do limite de requisições: quem recebe 401 ou 403 não recebe data nem 304. As actions
  e os métodos de escrita não passam por ela; `If-Unmodified-Since` numa escrita é ignorado.
  Evidência: `sapl/api/views.py:38-66`, `sapl/api/views.py:77-83`, `sapl/api/views.py:135-141`,
  `drfautoapi/drfautoapi.py:537`.
- API-GER-032 [implementado] No detalhe, a data é a do último registro de auditoria de criação ou
  alteração do objeto, buscado pelo tipo de conteúdo (app e model) e pelo id. Só há data quando o
  registro existe no `get_queryset` do viewset: id que não existe, ou que já foi excluído, responde
  404 sem data. Evidência: `sapl/api/views.py:115-124`.
- API-GER-033 [implementado] Na lista, a data é a do último registro de auditoria do model (app e
  model), de criação, alteração ou exclusão, qualquer que seja o filtro da requisição: toda
  gravação no model invalida todas as listas dele, e a exclusão de um item também. O registro de
  pesquisa da auditoria não conta. (executado) O cálculo custa uma consulta por lista e duas por
  detalhe, sem montar o filterset de novo. Evidência: `sapl/api/views.py:46`,
  `sapl/api/views.py:115-132`.
- API-GER-034 [implementado] Não há resposta condicional, nem data na resposta, em quatro casos: a
  rota tem visibilidade por registro (`get_queryset` próprio ou queryset filtrado, o critério de
  API-SER-026); a requisição traz `expand`; o model não tem registro de auditoria; ou a última
  gravação é do mesmo segundo da resposta, que a precisão de segundo do cabeçalho não distinguiria.
  Evidência: `sapl/api/views.py:84-105`.
- API-GER-035 [implementado] A resposta 200 com data leva `Last-Modified` e
  `Cache-Control: private, no-cache`: o cliente revalida a cada uso e cache intermediário não a
  guarda. Com `If-Modified-Since` igual ou posterior à data, a resposta é 304, sem corpo, com os
  mesmos dois cabeçalhos. Evidência: `sapl/api/views.py:52-75`.
- API-GER-036 [implementado] O viewset pode trocar o cálculo definindo `last_modified_func`. O de
  matéria usa a maior data entre a da auditoria e o campo `data_ultima_atualizacao`: a do model
  inteiro na lista e a da própria matéria no detalhe. Evidência: `sapl/api/views.py:107-113`,
  `sapl/api/views_materia.py:230-239`.
- API-GER-037 [implementado] O cálculo roda dentro do tratamento de erro do DRF. Valor inválido num
  filtro responde 400 em todas as rotas, inclusive `materia/materialegislativa` (API-FIL-010).
  Outro erro no cálculo vai para o log e a resposta sai sem data. Evidência:
  `sapl/api/views.py:92-98`.
- API-GER-038 [acordado] Limites da data, aceitos em 2026-11-22: ela só acompanha o que a
  auditoria registra. Não muda com gravação por `QuerySet.update()` ou `bulk_*`, por requisição
  anônima, nem nos models que a auditoria não acompanha; não muda quando muda um objeto
  relacionado de que a resposta depende (o `__str__`, por exemplo), nem quando mudam as permissões
  do usuário, que alteram os campos que ele recebe. Nesses casos quem revalida pode receber 304
  com dado desatualizado. Evidência: `cmj/core/signals_functions.py:30-74`,
  `sapl/api/views.py:107-132`.
- API-GER-039 [observado] (simulado) A busca da data da lista usa o índice da auditoria por app,
  model e data, criado para ela; a do detalhe usa o índice por tipo de conteúdo e id, que já
  existia. Numa tabela de rascunho com 5 milhões de linhas, no banco de teste, as duas responderam
  em menos de 0,1 ms. Sem o índice novo, a da lista levava 515 ms para um model com 62 mil
  registros, todos antigos. Criar o índice levou 9 s e ele ocupou 194 MB; a migration o cria
  bloqueando as gravações da auditoria nesse intervalo. Evidência: `cmj/core/models.py:337-349`,
  `cmj/core/migrations/0010_auditlog_core_auditl_app_nam_3221fa_idx.py:13-21`,
  `sapl/api/views.py:115-132`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1 a 7 de `docs/specs/README.md`, sobre o mecanismo de geração. Os
riscos de acesso, dados, filtros, custo e arquivos estão nas specs vizinhas.

Nenhum risco encontrado nos itens 1 a 7 (2026-11-22).

Itens sem achado nesta spec: 3 e 4 (o gerador não toca arquivos nem executa comandos) e 6 (lê só
`settings.DRFAUTOAPI`).

## Dúvidas

Nenhuma dúvida em aberto.

## Fora do escopo

- Quem alcança cada rota e por qual método: [acesso.md](./acesso.md).
- Campos devolvidos, `expand`, `include` e `exclude`: [serializacao.md](./serializacao.md).
- Filtros gerados e ordenação: [filtros.md](./filtros.md).
- Paginação, `get_all` e medições: [paginacao-custo.md](./paginacao-custo.md).
- Actions que servem arquivo e renderers: [arquivos.md](./arquivos.md).
- `DocumentoViewSet`, login (`docs/specs/api/login.md`), `recria_token` e `views_health.py`.
