# PortalCMJ

Portal legislativo da Câmara Municipal de Jataí-GO. Monolito Django 5.2 (Python 3.12) com
PostgreSQL 18 + pgvector, SAPL modificado (`sapl/`), apps próprios e CMS SIGAD (`cmj/`), API REST
gerada automaticamente (`drfautoapi/`) e dois frontends Vue (`_frontend/`).
Serviços: Redis (cache, broker, Channels), Solr 9.5 (Haystack), Celery + beat, Daphne (WebSocket).

Não há CI: `.github/` só contém instruções do Copilot, sem workflows. A validação é local.
Essas instruções têm erros conhecidos. Em caso de conflito, vale este arquivo e o código.

## Comandos

Rode Python no host, com o virtualenv do projeto ativo. Ele alcança os serviços do compose pelas
portas publicadas. Docker exige `sudo`.

```bash
# Ambiente completo: serviços, backend e os dois frontends em modo dev
sudo docker compose -f docker/docker-compose-dev.yaml up --build -d

# Django
python manage.py check
python manage.py makemigrations --check --dry-run   # sempre antes de criar migration
python manage.py makemigrations <app_label>
python manage.py migrate                            # em dev não roda ao subir o container
python manage.py runserver 0.0.0.0:9098             # backend no host (porta do launch.json)

# Testes (config em pyproject.toml: --no-migrations --reuse-db)
python -m pytest caminho/do/teste.py
python -m pytest caminho/do/teste.py::test_nome
python -m pytest caminho --create-db                # após mudar models
python -m pytest -m "not slow"

# Formatação Python: só nos arquivos alterados
python -m black <arquivos>
python -m isort --profile black <arquivos>

# Frontend (sem testes automatizados; o compose já mantém os dev servers no ar)
cd _frontend/v6    && npm run dev | build | lint | format
cd _frontend/v2018 && npm run serve | build | lint
```

`npm run lint` altera arquivos nos dois frontends (autofix).
`uupdev.sh`, `rdev.sh` e `ddev.sh` são locais e ignorados pelo git: não dependa deles.

| Serviço | Porta no host |
| --- | --- |
| Backend no container `cmj` | 9099 → 9000 |
| Vite (v6) / Webpack (v2018) | 5173 / 8080 |
| PostgreSQL / Redis / Solr | 5433 / 6379 / 8983 |

## Mapa do projeto

| Caminho | Conteúdo |
| --- | --- |
| `cmj/settings/` | Settings por tema; `project.py` agrega, `apps.py` tem `SAPL_APPS` e `CMJ_APPS` |
| `cmj/urls.py` | Único `ROOT_URLCONF` (`sapl/urls.py` não é usado) |
| `cmj/mixins.py`, `cmj/utils/` | Mixins de models e views, relatórios (`utils_report.py`), PDF, IA (`genia`) |
| `cmj/core` | `User`, auditoria, áreas de trabalho, OCR, rotas `/v6/` e `/app/` |
| `cmj/sigad` | CMS; `PathView` captura as URLs não tratadas |
| `cmj/arq`, `cmj/diarios` | Arquivo documental, diários oficiais |
| `cmj/loa` | LOA e emendas; `models/m_*`, `views/v_*`, `services/s_*` |
| `cmj/painelset` | Painéis e cronômetros de sessão, em tempo real |
| `cmj/search` | Busca, embeddings e chat RAG |
| `cmj/agenda`, `cerimonial`, `ouvidoria`, `videos`, `dashboard` | Módulos do portal |
| `cmj/api/` | `views_<app>.py`, `loa/`, serializers e filtros da API (`urls.py` está vazio) |
| `cmj/globalrules`, `sapl/rules` | Grupos e permissões (`map_rules.py`) |
| `sapl/crud/base.py` | `Crud`, `CrudAux`, `MasterDetailCrud` |
| `sapl/materia`, `sessao`, `norma`, `parlamentares`, `comissoes`, `protocoloadm`, `compilacao`, `audiencia`, `painel`, `base` | Núcleo legislativo |
| `sapl/api/urls.py` | Rotas `/api/` de SAPL **e** CMJ, schema e autenticação |
| `drfautoapi/` | Geração de ViewSets, serializers e filtros por model |
| `_templates/v2018/<app_label>/` | Templates Django e `layouts.yaml` (a maioria do HTML) |
| `_templates/v6/`, `_templates/vs/` | Shell do v6; `vs` só entra com `TEMPLATE_MODE=vs` |
| `_frontend/v6/` | Vue 3, Vite, Pinia, Bootstrap 5, bootstrap-vue-next |
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
  CRUD público usa `public = [RP_LIST, RP_DETAIL]`.
- **API**: `ApiViewSetConstrutor.build_class` gera `/api/<app_label>/<model>/` para os apps
  informados. Personalize com `@customize(Model)` em `cmj/api/views_<app>.py`,
  `cmj/api/loa/views/` ou `sapl/api/views_<app>.py`. Módulo novo em `cmj/api` precisa entrar em
  `import_modules` de `cmj/api/views.py`. Serializers herdam `CmjSerializerMixin`.
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

O código novo vai para o **v6**. O v2018 é só manutenção: não migre para Vue 3 nem Pinia.

| | v6 | v2018 |
| --- | --- | --- |
| Rota Django | `/v6/<slug>` → `base_v6.html` | `/app/<slug>` → `app_vue_v2018.html` |
| Integração | `django_vite` | `webpack_loader` |
| Alias | `~@/` | `@/` |
| Componente | `<script setup>` | Options API |
| Estado | `useSyncStore`, `useAuthStore`, `useMessageStore` | Vuex |
| EventBus | `inject('EventBus')` | `import { EventBus } from '@/event-bus'` |
| HTTP | `Resources.Utils.fetch({ app, model, id })` | `Resources.Utils.getModel(app, model, id)` |

- Componente **novo** no v6 segue a ordem de seções em `<script setup>`: `// 1. Imports`,
  `// 2. Composables`, `// 3. Props & Emits`, `// 4. State & Refs`, `// 5. Computed Properties`,
  `// 6. Watchers`, `// 7. Events & Lifecycle Hooks`, `// 8. Functions`. Não reordene os existentes.
- Nos dois, `_` (lodash) e `$` são globais injetados. No v6 a injeção não cobre `src/routers/`.
- Cache sincronizado: `data_cache?.<app>_<model>?.[id]`, preenchido por `fetchSync`.
- No v2018 só `store__sync` tem namespace. `store__auth`, `store__message` e `store__online` são
  globais: use `mapGetters` e `mapActions(['sendMessage'])`.
- Remova listeners do EventBus ao desmontar o componente.

## Armadilhas do legado

- **Ordem das URLs importa**: quase tudo é incluído com prefixo vazio e `cmj.sigad.urls` é o
  catch-all final. `APPEND_SLASH = False`: a barra final precisa bater com o padrão.
- **Signals globais**: auditoria e rede social escutam `post_save` de todos os models.
  `QuerySet.update()` e `bulk_*` não disparam signals nem atualizam `search`.
- **Testes sem banco falham**: a fixture autouse de `conftest.py` acessa o banco, e teste sem
  `django_db` termina com `Database access not allowed`.
- **Views SQL não existem nos testes**: `--no-migrations` ignora `RunSQL`, o que afeta os models
  `managed = False` em `sapl/materia/models.py` e `cmj/loa/models/m_financeiro_orcamento.py`.
- **`--reuse-db`**: mudança de model exige `--create-db`.
- **Testes ignorados**: veja `collect_ignore_glob` em `conftest.py`.
- **Cache em DEBUG é `DummyCache`**: locks com `cache.add` sempre passam e nada fica em cache.
- **Host x container**: fora do container, alguns fluxos executam a função da task de forma
  síncrona em vez de enfileirar (`FOLDER_DEBUG_CONTAINER`).
- **`dev-webpack-stats.json` velho** faz o Django apontar para o Webpack em :8080 mesmo com ele
  desligado. Com o dev server parado, remova esse arquivo.
- **`dist/` é versionado** nos dois frontends e vai para a imagem de produção. Commits de
  funcionalidade não incluem rebuild; ele sai em commits "rebuild frontends".
- **Produção roda `migrate` ao subir** (`docker/start.sh`), com containers blue e green.
  Prefira migrations compatíveis com a versão ainda em execução.
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
- Não edite `.github/`, `collected_static/`, `__notebooks_private/`, `cmj/legacy_cep/`.
- Não reformate arquivos inteiros fora do escopo da tarefa.

## Documentação

- `docs/specs/README.md`: convenções das specs (marcadores, IDs, varredura de segurança,
  publicação). Leia antes de criar ou alterar uma spec. Skills: `spec-legado` para comportamento
  existente, `spec-nova` para funcionalidade nova.
- `docs/rag/README.md`: índice do chat RAG, com arquitetura, ingestão, recuperação, WebSocket/LLM,
  modelos, operação, diagnóstico e avaliação (`docs/rag/01` a `08`). Leia antes de mexer em `cmj/search`.
- `docs/commands/ocrmypdf_command.md`: command `ocrmypdf`.
- `docs/backend/convencoes.md`: exemplos de CRUD, mixins, API, permissões, testes e novo app.
- `docs/frontend/v6.md`: stores, `Resources.Utils`, rotas e padrões do v6.
- `docs/frontend/v2018.md`: Vuex, `Resources.Utils` e padrões do v2018.
- `docs/specs/loa/fases-emenda.md`: comportamento atual das fases da emenda. Leia antes de alterá-las.
- `docs/specs/loa/edicao-emenda.md`: telas de criação e edição da emenda, API usada por elas e
  autosave. Leia antes de alterar essas telas.
- `docs/specs/loa/edicao-agrupamento.md`: tela de edição do agrupamento, registros contábeis,
  emendas coletivas e autosave. Leia antes de alterar essa tela.
- `docs/specs/loa/listagem-emendas.md`: listagem das emendas da LOA, filtros, cache do cartão, PDF da
  listagem e dependências do v2018. Leia antes de alterar essa tela.

## A confirmar

- Setup do zero: não há `.env.example`, e `DATABASE_URL_DEV` é obrigatória com `DEBUG=True`.
- Processo de rebuild dos frontends e de deploy blue/green.
- Execução de `manage.py` e `pytest` dentro do container `cmj` (só o host foi verificado).
