# Instruções do GitHub Copilot para o Portal CMJ

Sistema Django para a Câmara Municipal de Jataí (CMJ). Dois pacotes de backend (`cmj/`, `sapl/`) + frontend em Vue dual.

## Comandos

| Tarefa | Comando | Descrição |
|--------|---------|-----------|
| Iniciar ambiente de desenvolvimento | `./uupdev.sh` | Inicializa o ambiente de desenvolvimento a partir do docker-compose-dev.yaml onde estão definidos os serviços necessários para o backend e os dois frontend |
| Executar testes | `pytest` (configuração em `pyproject.toml`) | Executa a suíte de testes |
| Desenvolvimento do frontend v6 | `cd _frontend/v6 && npm run dev` (Vite, porta 5173) | Inicia o servidor de desenvolvimento do frontend v6 (Atenção ao compose dev: Se foi utilizado o docker-compose-dev.yaml, o servidor Vite já está em execução e não é necessário iniciá-lo manualmente) |
| Desenvolvimento do frontend v2018 | `cd _frontend/v2018 && npm run serve` (Webpack, porta 8080) | Inicia o servidor de desenvolvimento do frontend v2018 (Atenção ao compose dev: Se foi utilizado o docker-compose-dev.yaml, o servidor Webpack já está em execução e não é necessário iniciá-lo manualmente) |

- Os testes usam `--no-migrations --reuse-db`;

## Arquitetura

### Backend
- **`cmj/`** — aplicativos do portal: `agenda`, `arq`, `cerimonial`, `core`, `dashboard`, `diarios`, `loa`, `ouvidoria`, `painelset`, `search`, `sigad`, `videos`
- **`sapl/`** — núcleo legislativo (legado pesado): `materia`, `sessao`, `norma`, `parlamentares`, `compilacao`, `comissoes`, `audiencia`, `base`, `painel`, `protocoloadm`
- URLs: `cmj/urls.py` agrega todas as rotas;

### Frontend (`_frontend/`)
- **`v6/`** ← **Preferência para novas funcionalidades**: Vue 3, Vite, Pinia, Bootstrap 5
- **`v2018/`** — Manutenção apenas: Vue 2, Webpack, Bootstrap 4
- Os assets compilados são servidos em `collected_static/`; os templates do Django atuam como shell para os apps Vue

## Configuração

- As configurações estão divididas em `cmj/settings/`: `project.py` (ponto de entrada), `__init__.py`, `apps.py`, `auth.py`, `drf.py`, `email.py`, `fake.py`, `frontend.py`, `languages.py`, `logs.py`, `medias.py`, `middleware.py`, `zenv.py`
- Variáveis de ambiente devem ser definidas em um dos arquivos de configuração em `cmj/settings/` e carregadas com config que deve é importado em todos os arquivos de `cmj/settings/`, garantindo que todas as partes do projeto tenham acesso às mesmas configurações de ambiente.
- Arquivo `cmj/settings/fake.py` contém configurações específicas para execução de collectstatic feito em `docker/Dockerfile`, garantindo que os assets estáticos sejam corretamente coletados durante o build da imagem Docker, sem impactar as configurações de ambiente de produção.

## Padrões principais

- **Classes base de CRUD**: `sapl/crud/` — usadas em vários apps do sapl
- **Busca**: Haystack + Solr (`cmj/haystack.py`); verificar `search_indexes.py` em cada app.
- **API**: DRF em `cmj/api/` e `sapl/api/`
- **Relatórios em PDF**: `cmj/utils/utils_report.py`
- **Layouts de formulário**: `sapl/crispy_layout_mixin.py`
- **Stores do frontend** (v6): `SyncStore` (cache de dados + WebSocket), `AuthStore`, `MessageStore` — consulte [`/.github/instructions/frontend-v6.instructions.md`](/.github/instructions/frontend-v6.instructions.md)
