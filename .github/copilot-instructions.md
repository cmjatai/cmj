# GitHub Copilot Instructions for CMJ Portal

Django system for the Câmara Municipal de Jataí (CMJ). Two backend packages (`cmj/`, `sapl/`) + dual Vue frontend.

## Commands

| Task | Command |
|------|---------|
| Start dev env | `./ddev.sh` |
| Run tests | `pytest` (config in `pyproject.toml`) |
| Frontend v6 dev | `cd _frontend/v6 && yarn dev` (Vite, port 5173) |
| Frontend v2018 dev | `cd _frontend/v2018 && yarn serve` (Webpack, port 8080) |

- Tests use `--no-migrations --reuse-db`; settings: `cmj/settings/fake.py`
- Notebooks: use `django_setup.py` to initialize Django (`__notebooks/`, `__notebooks_private/`)

## Architecture

### Backend
- **`cmj/`** — Portal apps: `agenda`, `arq`, `cerimonial`, `core`, `dashboard`, `diarios`, `loa`, `ouvidoria`, `painelset`, `search`, `sigad`, `videos`
- **`sapl/`** — Legislative core (legacy-heavy): `materia`, `sessao`, `norma`, `parlamentares`, `compilacao`, `comissoes`, `audiencia`, `base`, `painel`, `protocoloadm`
- URLs: `cmj/urls.py` aggregates all routes; `sapl` prefixed at `/sapl/`

### Frontend (`_frontend/`)
- **`v6/`** ← **Prefer for new features**: Vue 3, Vite, Pinia, Bootstrap 5
- **`v2018/`** — Maintenance only: Vue 2, Webpack, Bootstrap 4
- Built assets served from `collected_static/`; Django templates act as shell for Vue apps

## Configuration

- Settings split across `cmj/settings/`: `project.py` (entry point), `apps.py`, `drf.py`, `auth.py`, `middleware.py`, `email.py`, `medias.py`, `fake.py` (tests)
- Env vars via `python-decouple` → `security.json`

## Key Patterns

- **CRUD base classes**: `sapl/crud/` — used across sapl apps
- **Search**: Haystack + Solr (`cmj/haystack.py`); check `search_indexes.py` per app
- **API**: DRF in `cmj/api/` and `sapl/api/`
- **PDF reports**: `cmj/utils_report.py`
- **Form layouts**: `sapl/crispy_layout_mixin.py`
- **Frontend stores** (v6): `SyncStore` (data cache + WebSocket), `AuthStore`, `MessageStore` — see [`/memories/repo/v6_frontend_patterns.md`](/memories/repo/v6_frontend_patterns.md)
- **Test infrastructure details**: see [`/memories/repo/test_infrastructure.md`](/memories/repo/test_infrastructure.md)
