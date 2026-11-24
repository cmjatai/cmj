# PortalCMJ

Portal legislativo da Câmara Municipal de Jataí-GO. Monolito Django 5.2 (Python 3.12) com
PostgreSQL 18 + pgvector, SAPL modificado (`sapl/`), apps próprios e CMS SIGAD (`cmj/`), API REST
gerada automaticamente (`drfautoapi/`) e três frontends Vue (`_frontend/`).
Serviços: Redis (cache, broker, Channels), Solr 9.5 (Haystack), Celery + beat, Daphne (WebSocket).

CI: `.github/workflows/ci.yml` roda o `specs_check` e os testes do v8 e do v2018 (`npm test`) no GitHub
Actions (runner padrão, grátis em repositório público), em push e PR para o `master`. O resto da
validação é local.

## Comandos

Rode Python no host, com o virtualenv do projeto ativo. Ele alcança os serviços do compose pelas
portas publicadas. Docker exige `sudo`.

```bash
# Ambiente completo: serviços, backend e os três frontends em modo dev
sudo docker compose -f docker/docker-compose-dev.yaml up --build -d

# Django
python manage.py check
python manage.py makemigrations --check --dry-run   # sempre antes de criar migration
python manage.py makemigrations <app_label>
python manage.py migrate                            # em dev não roda ao subir o container
python manage.py runserver 0.0.0.0:9098             # backend no host (porta do launch.json)
python manage.py specs_check                        # consistência das specs com testes e código

# Testes (config em pyproject.toml: --no-migrations --reuse-db)
python -m pytest caminho/do/teste.py
python -m pytest caminho/do/teste.py::test_nome
python -m pytest caminho --create-db                # após mudar models
python -m pytest -m "not slow"

# Formatação Python: só nos arquivos alterados
python -m black <arquivos>
python -m isort --profile black <arquivos>

# Frontend (o compose já mantém os dev servers no ar; v8 e v2018 têm testes automatizados)
cd _frontend/v6    && npm run dev | build | lint | format
cd _frontend/v8    && npm run dev | build | lint | format | test
cd _frontend/v2018 && npm run serve | build | lint | test
```

`npm run lint` altera arquivos nos três frontends (autofix).
`uupdev.sh`, `rdev.sh` e `ddev.sh` são locais e ignorados pelo git: não dependa deles.

| Serviço | Porta no host |
| --- | --- |
| Backend no container `cmj` | 9099 → 9000 |
| Vite (v6) / Vite (v8) / Webpack (v2018) | 5173 / 5174 / 8080 |
| PostgreSQL / Redis / Solr | 5433 / 6379 / 8983 |
| Prometheus / Grafana (só em 127.0.0.1) | 9090 / 3000 |

Produção simulada (imagem da produção, isolada do dev, só localhost): `sudo docker/prodsim/up.sh`,
`smoke.sh`, `db-from-dev.sh` e `down.sh`. Portal em `https://localhost:8443`, Grafana em 3001 e
Prometheus em 9091. Detalhes em `docs/backend/monitoramento.md`.

## Mapa do projeto

| Caminho | Conteúdo |
| --- | --- |
| `cmj/settings/` | Settings por tema; `project.py` agrega, `apps.py` tem `SAPL_APPS` e `CMJ_APPS` |
| `cmj/urls.py` | Único `ROOT_URLCONF` (`sapl/urls.py` não é usado) |
| `cmj/mixins.py`, `cmj/utils/` | Mixins de models e views, relatórios (`utils_report.py`), PDF, IA (`genia`) |
| `cmj/core` | `User`, auditoria, áreas de trabalho, OCR, rotas `/v6/`, `/v8/` e `/app/` |
| `cmj/sigad` | CMS; `PathView` captura as URLs não tratadas |
| `cmj/arq`, `cmj/diarios` | Arquivo documental, diários oficiais |
| `cmj/loa` | LOA e emendas; `models/m_*`, `views/v_*`, `services/s_*` |
| `cmj/painelset` | Painéis e cronômetros de sessão, em tempo real |
| `cmj/search` | Busca, embeddings e chat RAG |
| `cmj/agenda`, `cerimonial`, `ouvidoria`, `videos`, `dashboard` | Módulos do portal |
| `cmj/v8` | Lado Django do frontend v8: rotas `^v8/`, views, tags e `services/s_*`; sem models |
| `cmj/api/` | `views_<app>.py`, `loa/`, serializers e filtros da API (`urls.py` está vazio) |
| `cmj/globalrules`, `sapl/rules` | Grupos e permissões (`map_rules.py`) |
| `sapl/crud/base.py` | `Crud`, `CrudAux`, `MasterDetailCrud` |
| `sapl/materia`, `sessao`, `norma`, `parlamentares`, `comissoes`, `protocoloadm`, `compilacao`, `audiencia`, `painel`, `base` | Núcleo legislativo |
| `sapl/api/urls.py` | Rotas `/api/` de SAPL **e** CMJ, schema e autenticação |
| `drfautoapi/` | Geração de ViewSets, serializers e filtros por model |
| `_templates/v2018/<app_label>/` | Templates Django e `layouts.yaml` (a maioria do HTML) |
| `_templates/v6/` | Shell do v6 (`base_v6.html`) |
| `_templates/v8/` | `base_v8.html` na raiz; layouts, shell, parciais e páginas do v8 em `v8/` |
| `_templates/vs/` | Só entra com `TEMPLATE_MODE=vs` |
| `_frontend/v6/` | Vue 3, Vite, Pinia, Bootstrap 5, bootstrap-vue-next |
| `_frontend/v8/` | Vue 3, Vite 8, Pinia, Reka UI, Tailwind v4; híbrido com o Django, por ilhas e zonas SPA |
| `_frontend/v2018/` | Vue 2, Vue CLI/Webpack, Vuex, BootstrapVue |
| `docker/` | Compose, Dockerfiles, `start*.sh`, nginx |
| `solr/` | Configsets `cmj_configset` e `arq_configset` |

Fora de uso: `cmj/legacy_cep`, `cmj/checklist` e `sapl/lexml` não estão em `INSTALLED_APPS`.
`sapl/relatorios` também não está, mas suas URLs e templates são usados.

## Convenções do backend

- **Telas CRUD**: use `sapl.crud.base`. `Crud.build(Model, "help")`, `CrudAux.build(...)` para
  tabelas auxiliares (exige `base.view_tabelas_auxiliares`), `MasterDetailCrud` para pai-filho.
- **Formulários de CRUD**: os campos vêm de `_templates/v2018/<app_label>/layouts.yaml`. Model novo
  em CRUD precisa de entrada nesse arquivo.
- **URLs**: `app_name = AppConfig.name`, logo o namespace é `sapl.materia` ou `cmj.loa`. Use
  `re_path` e registre o módulo em `cmj/urls.py`, antes de `cmj.sigad.urls`.
- **Apps**: `AppConfig` com `name` (`cmj.x`) e `label` (`x`); registre em `SAPL_APPS` ou `CMJ_APPS`.
- **Models**: `CmjModelMixin` dá `created`/`modified` e chama `clean()` no `save()`.
  `CmjAuditoriaModelMixin` acrescenta `owner`/`modifier`.
- **Busca no banco**: `CmjSearchMixin` preenche `search` a partir de `fields_search`, que aceita
  campo, `rel__campo` ou método `hook_*`. Busca Solr é outro mecanismo, descrito abaixo.
- **Permissões**: radicais `RP_LIST`, `RP_DETAIL`, `RP_ADD`, `RP_CHANGE`, `RP_DELETE`. Grupos em
  `cmj/globalrules/map_rules.py` ou `sapl/rules/map_rules.py`, aplicados no `post_migrate`.
  CRUD público usa `public = [RP_LIST, RP_DETAIL]`. O terceiro elemento da regra no `map_rules`
  torna o model público na API e no WebSocket, sem depender do `public` do CRUD: os dois têm de
  concordar.
- **API**: `ApiViewSetConstrutor.build_class` gera `/api/<app_label>/<model>/` para os apps
  informados. Personalize com `@customize(Model)` em `cmj/api/views_<app>.py`,
  `cmj/api/loa/views/` ou `sapl/api/views_<app>.py`. Módulo novo em `cmj/api` precisa entrar em
  `import_modules` de `cmj/api/views.py`. Serializers herdam `CmjSerializerMixin`. Campo que não
  pode sair para todos é retirado na classe do serializer (`get_fields`), não no viewset: `expand`
  e as actions usam a classe, e filtro e ordenação gerados só valem para campo que o serializer
  entrega ao usuário. O `CmjSerializerMixin` já aplica a todas as rotas: num model com o par `ip`
  e `user` (quem fez o registro), os dois campos só saem para superusuário, assim como as chaves
  de armazenamento dentro de `metadata` (`s3_aws`, `s3_cmj`, `locaweb`); as demais relações com o
  model de usuário só saem para quem tem `list_` do model; e `owner` e `modifier` são preenchidos
  pelo servidor nas gravações, sem aceitar valor do cliente. A visibilidade dos registros de um model fica no `get_queryset` do viewset,
  com a regra numa classe de serviço do app (exemplo: `sapl/compilacao/services/s_visibilidade.py`);
  o `expand` e as actions de arquivo consultam esse ponto, e o canal de sincronização por WebSocket
  manda o aviso desses models sem o conteúdo do registro. Os módulos de serializers e de filtersets
  não importam `sapl.api.views`: módulo configurado que não importa, ou que é lido pela metade,
  interrompe a inicialização, assim como classe achada pelo nome com `Meta.model` de outro app.
  `get_all=true` só devolve a lista inteira até `API_GET_ALL_MAX_ITEMS` (2.000)
  para quem não tem `list_` do model: tela pública que use `get_all` precisa filtrar por um
  registro pai. `expand` aceita até 8 caminhos por requisição; acima disso a resposta é 400.
  O model de usuário e o registro de auditoria não têm rota na API (`core/user`,
  `core/auditlog`): contas, senhas, grupos e permissões ficam nas telas de usuário, e a auditoria,
  na tela de pesquisa. A auditoria não guarda o campo `password` (`AuditoriaService`).
- **Celery**: toda task declara `queue=`: `cq_arq`, `cq_core`, `cq_videos`, `cq_base` ou
  `cq_painelset`. Fila nova exige alterar os `docker/start*.sh`.
- **Solr**: índices só em `cmj/search/search_indexes.py` e `cmj/arq/search_indexes.py`. Model novo
  entra também em `MODELS_SOLR_*` de `cmj/haystack.py`.
- **WebSocket**: `consumers.py` e `routing.py` em `core`, `painelset` e `search`, somados em `cmj/asgi.py`.
- **Camadas**: no legado, a lógica fica em views, models, forms e signals; não a mova sem pedido.
  Funcionalidade nova concentra a regra de negócio em `<app>/services/s_*.py`, no app mais
  adequado, e views, API, forms e frontend fazem só o essencial. Detalhes na skill `spec-nova`.
- **Ambiente**: leia variáveis com `config` de `cmj/settings/zenv.py`.
- **Estilo Python**: black (padrão, sem config no repo) e isort com `--profile black`.

## Convenções do frontend

O código novo vai para o **v6**. O v2018 é manutenção, mas continua em uso a médio e longo prazo:
não migre para Vue 3 nem Pinia e não crie nele módulo ou entrada novos. Funcionalidade nova que
complementa uma tela do v2018 pode ser feita nele quando for urgente e a migração não couber no prazo.
O **v8** é a arquitetura híbrida que vai substituir o v6 e o v2018. Por ora tem a demonstração, o
design system (`/v8/ds/`, com temas nomeados e componentes base sobre o Reka UI) e nenhuma tela
real: só mexa nele quando a tarefa pedir, e leia `docs/frontend/v8.md` antes.

| | v6 | v2018 |
| --- | --- | --- |
| Rota Django | `/v6/<slug>` → `base_v6.html` | `/app/<slug>` → `app_vue_v2018.html` |
| Integração | `django_vite` | `webpack_loader` |
| Alias | `~@/` | `@/` |
| Componente | `<script setup>` | Options API |
| Estado | `useSyncStore`, `useAuthStore`, `useMessageStore` | Vuex |
| EventBus | `inject('EventBus')` | `import { EventBus } from '@/event-bus'` |
| HTTP | `Resources.Utils.fetch({ app, model, id })` | `Resources.Utils.getModel(app, model, id)` |

- **v8**: rotas `^v8/` em `cmj/v8/urls.py`; o Django renderiza a página e o Vue entra em ilhas
  (`{% v8_island %}`) e zonas SPA, com um único app montado em `#cmj-v8-app`. O HTML do Django não é
  compilado como template Vue. Usa o alias `~@/` e `<script setup>`. Drawers, modals e toasts vêm
  de `~@/overlays/`, e toda requisição passa por `~@/http/client`. Não tem Bootstrap, jQuery nem
  axios. Tudo o que o v8 cria fica contido em `/v8/`.
- Componente **novo** no v6 e no v8 segue a ordem de seções em `<script setup>`: `// 1. Imports`,
  `// 2. Composables`, `// 3. Props & Emits`, `// 4. State & Refs`, `// 5. Computed Properties`,
  `// 6. Watchers`, `// 7. Events & Lifecycle Hooks`, `// 8. Functions`. Não reordene os existentes.
- No v6 e no v2018, `_` (lodash) e `$` são globais injetados. No v8 só `_`: não há jQuery nem
  Bootstrap. No v6 a injeção não cobre `src/routers/`.
- Cache sincronizado: `data_cache?.<app>_<model>?.[id]`, preenchido por `fetchSync`.
- No v2018 só `store__sync` tem namespace. `store__auth`, `store__message` e `store__online` são
  globais: use `mapGetters` e `mapActions(['sendMessage'])`.
- Remova listeners do EventBus ao desmontar o componente.

## Armadilhas do legado

- **Ordem das URLs importa**: quase tudo é incluído com prefixo vazio e `cmj.sigad.urls` é o
  catch-all final. `APPEND_SLASH = False`: a barra final precisa bater com o padrão.
- **`_templates/v8` é consultado antes de `_templates/v2018`**: um arquivo como `base.html` ou
  `404.html` na raiz dele encobre o do portal. Template do v8 vai em `_templates/v8/v8/`.
- **Signals globais**: auditoria e rede social escutam `post_save` de todos os models.
  `QuerySet.update()` e `bulk_*` não disparam signals nem atualizam `search`.
- **Testes sem banco falham**: a fixture autouse de `conftest.py` acessa o banco, e teste sem
  `django_db` termina com `Database access not allowed`.
- **Views SQL não existem nos testes**: `--no-migrations` ignora `RunSQL`, o que afeta os models
  `managed = False` em `sapl/materia/models.py` e `cmj/loa/models/m_financeiro_orcamento.py`.
- **`--reuse-db`**: mudança de model exige `--create-db`. O banco de teste é por checkout: `test_cmj`
  no principal e `test_cmj_<nome>` em cada worktree de `cmj.worktrees/<nome>` (`DATABASE_TEST_NAME`
  sobrescreve).
- **Testes ignorados**: veja `collect_ignore_glob` em `conftest.py`.
- **Cache em DEBUG é `DummyCache`**: locks com `cache.add` sempre passam e nada fica em cache.
- **Host x container**: fora do container, alguns fluxos executam a função da task de forma
  síncrona em vez de enfileirar (`FOLDER_DEBUG_CONTAINER`).
- **`dev-webpack-stats.json` velho** faz o Django apontar para o Webpack em :8080 mesmo com ele
  desligado. Com o dev server parado, remova esse arquivo.
- **`DJANGO_VITE_DEV_MODE` vale para v6 e v8 juntos**: ligada, o Django aponta para os dev
  servers em 5173 e 5174; desligada, lê os `dist/`, e mudança em `src/` só aparece após build.
- **`dist/` é versionado** nos três frontends e vai para a imagem de produção. O branch de uma
  tarefa completa inclui o rebuild dos três frontends e entra no `master` num commit só (squash):
  cada push no `master` gera uma tag de versão (`docs/specs/infra/versionamento.md`), e a versão
  tem de trazer o código e o `dist/` dele juntos.
- **`package-lock.json` é versionado** nos três frontends e o CI instala com `npm ci`. O rebuild
  regenera o lock. Commit que muda um `package.json` leva o lock junto.
- **`.npmrc` com `min-release-age=7`** nos três frontends: o npm recusa versão publicada há menos
  de 7 dias. `rm package-lock.json && npm install` não atualiza o que já está em `node_modules`;
  para renovar versões use `npm update`.
- **Produção roda `migrate` ao subir** (`docker/start.sh`), com containers blue e green.
  Prefira migrations compatíveis com a versão ainda em execução.
- **IP do cliente**: a aplicação lê `X-Real-IP`. O nginx do container o define nos três blocos de
  proxy (telas, API e WebSocket) e só aceita o valor do proxy da frente em conexão local ou
  privada (`real_ip_header`). Não redefina o cabeçalho num bloco só.
- **Settings ignoradas**: `USE_SOLR`, `SOLR_URL` e `SOLR_COLLECTION` são fixas em `project.py`.
- **`requirements/dev-requirements.txt`** fixa versões de `pandas` diferentes de `requirements.txt`.

## O que não fazer

- Não edite migrations já commitadas nem escreva migration à mão. Gere com `makemigrations`; para
  dados ou SQL, parta de `makemigrations --empty <app_label>`.
- Se o `--dry-run` mostrar mudanças alheias à tarefa, avise em vez de incluí-las.
- Não leia nem commite `.env`, `security.json`, `*.pfx` ou credenciais.
- Não use `DATABASE_URL_PRD` nem suba `docker/docker-compose.yaml` sem pedido explícito.
- Não execute sem pedido: `restore_cmj_dev.sh` (apaga o banco), `docker/restore-db.sh`, `s3_restore`.
- Não rode `npm run build` nem commite `dist/` sem pedido.
- Não escreva teste nem script que comunique com API externa (Telegram, YouTube, S3 pelo `boto3`,
  `google.genai`), nem com chave vazia: troque o cliente por mock. O `conftest.py` já impede o
  envio do signal de rede social (`_rede_social_nao_envia_nos_testes`) e barra, em todo `pytest`,
  a conexão por socket Python a destino que não seja local ou de rede privada (`vigia_de_rede`):
  o teste que tenta é reprovado, mesmo que o código engula o erro. Script fora do `pytest` não
  tem essa proteção.
- Não edite `collected_static/`, `__notebooks_private/`, `cmj/legacy_cep/`.
- Não reformate arquivos inteiros fora do escopo da tarefa.

## Documentação

- `docs/specs/README.md`: convenções das specs (marcadores, IDs, checagem com `specs_check`,
  varredura de segurança, publicação). Leia antes de criar ou alterar uma spec. Skills: `spec-legado` para comportamento
  existente, `spec-nova` para funcionalidade nova.
- `docs/tutorials/rag/README.md`: índice do chat RAG, com arquitetura, ingestão, recuperação,
  WebSocket/LLM, modelos, operação, diagnóstico e avaliação (`docs/tutorials/rag/01` a `08`). Leia
  antes de mexer em `cmj/search`.
- `docs/commands/ocrmypdf_command.md`: command `ocrmypdf`.
- `docs/backend/convencoes.md`: exemplos de CRUD, mixins, API, permissões, testes e novo app.
- `docs/backend/monitoramento.md`: Prometheus, Grafana e exporters (dev e produção), métricas em
  modo multiprocess, acesso aos endpoints de operação e produção simulada. Leia antes de mexer em
  `docker/`, no `/metrics` ou no `EndpointRestrictionMiddleware`.
- `docs/frontend/v6.md`: stores, `Resources.Utils`, rotas e padrões do v6.
- `docs/frontend/v8.md`: qual modo de tela usar, layouts e blocks dos templates, tags e atributos do
  lado Django, composables do lado Vue, CSS e testes. Leia antes de mexer em `_frontend/v8`, `_templates/v8` ou `cmj/v8`.
- `docs/specs/infra/endpoints-operacao.md`: quem alcança `/metrics`, `/health/`, `/ready/`, `/version/`
  e `/nginx_status` (nginx do container e `EndpointRestrictionMiddleware`). Leia antes de alterá-los.
- `docs/specs/infra/versionamento.md`: versão do backend (`vAAAA.MM.N`, do git, em
  `PORTALCMJ_VERSION` e na tag que o CI cria a cada push no master) e dos frontends
  (`<frontend>.AAAA.MM.N`, incrementada pelo `prebuild` e gravada no service worker).
- `docs/specs/api/login.md`: login por usuário e senha pela API (`/api/auth/session` e
  `/api/auth/token`): limite de tentativas e token CSRF. Leia antes de alterar essas rotas.
- `docs/specs/api/`: comportamento atual da API gerada pelo `drfautoapi`, em seis specs. Leia a da
  parte que for alterar, e todas antes de expor um model novo na API: `gerador.md` (registro,
  `@customize`, rotas e `Last-Modified`), `acesso.md` (permissões, o que anônimo alcança e
  visibilidade dos registros), `serializacao.md` (campos por padrão, `expand`, `include` e
  `exclude`), `filtros.md` (filtros e ordenação gerados), `paginacao-custo.md` (`get_all`, medições
  e quem usa `get_all` nos frontends) e `arquivos.md` (`ResponseFileMixin` e renderers).
- `docs/specs/v8/README.md`: índice das specs do v8 (arquitetura, templates em camadas, shell,
  overlays, cliente HTTP, demonstração, temas, design system e componentes base). Leia a spec da
  parte que for alterar.
- `docs/frontend/v2018.md`: Vuex, `Resources.Utils`, padrões e testes do v2018.
- `docs/specs/v2018/README.md`: índice das specs do v2018 (estrutura do projeto webpack e
  infraestrutura de testes). Leia antes de mexer em `vue.config.js`, nas entradas ou em
  `_frontend/v2018/tests`.
- `docs/specs/loa/fases-emenda.md`: comportamento atual das fases da emenda. Leia antes de alterá-las.
- `docs/specs/loa/edicao-emenda.md`: telas de criação e edição da emenda, API usada por elas e
  autosave. Leia antes de alterar essas telas.
- `docs/specs/loa/edicao-agrupamento.md`: tela de edição do agrupamento, registros contábeis,
  emendas coletivas e autosave. Leia antes de alterar essa tela.
- `docs/specs/loa/listagem-emendas.md`: listagem das emendas da LOA, filtros, cache do cartão, PDF da
  listagem e dependências do v2018. Leia antes de alterar essa tela.
- `docs/specs/loa/prestacao-contas-tela.md`: lado Django de `/loa/<pk>/prestacaoconta`: rota, gate do
  reCAPTCHA, relatório para impressão (`?print=True`) e `InfoFilterMixin`. Leia antes de alterar a
  view, os templates do relatório ou o mixin do reCAPTCHA.
- `docs/specs/loa/prestacao-contas-consulta.md`: consulta consolidada da prestação de contas
  (`PrestacaoContaService` e as actions `prestacaoconta_resumo`, `_dashboard` e `_itens` de
  `loa/loa`): valor de cada item, totalização, execução, dashboard e lista paginada. Leia antes de
  alterar o cálculo de valores da prestação de contas; a regra fica no serviço, não no frontend.
- `docs/specs/loa/prestacao-contas-painel.md`: painel Vue da prestação de contas no v2018
  (`modules/loa/pcl`): filtros, busca, cache, cartões, abas, totalização, dashboard e a API
  consumida. Leia antes de alterar esses componentes.
- `docs/tutorials/README.md`: índice dos tutoriais. Tutorial explica e não define regra: as regras
  ficam nas specs. O de `frontend/v8` é material de aprendizado para quem está chegando: para
  implementar no v8, use `docs/frontend/v8.md` e as specs. O de `rag` é o que a linha do chat RAG,
  acima, manda ler.

## A confirmar

- Setup do zero: não há `.env.example`, e `DATABASE_URL_DEV` é obrigatória com `DEBUG=True`.
- Processo de rebuild dos frontends e de deploy blue/green.
- Execução de `manage.py` e `pytest` dentro do container `cmj` (só o host foi verificado).
