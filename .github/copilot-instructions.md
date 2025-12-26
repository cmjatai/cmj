# GitHub Copilot Instructions for CMJ Portal

## Architecture Overview

This project is a complex Django-based system for the "Câmara Municipal de Jataí" (CMJ). It consists of two main backend components and a dual-stack frontend.

### Backend Components
- **`cmj/` (Portal):** The main Django project containing modern apps (`agenda`, `ouvidoria`, `diarios`, etc.) and project configuration.
- **`sapl/` (Legislative Core):** A massive, legacy-heavy application handling legislative processes (`materia`, `sessao`, `norma`, `parlamentares`). This is the core business logic.
- **Integration:** `sapl` is integrated as a folder within the workspace but functions like a standalone app suite.

### Frontend Architecture
The project maintains two co-existing frontend stacks in `_frontend/`:
1.  **`v2026` (Modern):** Vue 3, Vite, Pinia, Bootstrap 5. Used for new features and gradual migration.
2.  **`v2018` (Legacy):** Vue 2, Webpack, Bootstrap 4. Contains the bulk of existing UI logic.

**Guideline:** When implementing new UI features, prefer **`v2026`** (Vue 3). Only touch `v2018` for maintenance of legacy views.

## Development Workflow

### Environment Management
- **Entry Point:** `ddev.sh` is the primary script for managing the dev environment.
    - Usage: `./ddev.sh` (starts/restarts services).
    - It wraps `docker compose -f docker/docker-compose-dev.yaml`.
- **Docker Services:**
    - `cmjredis`: Redis for caching and Celery.
    - `cmjsolr`: Solr 9.5 for search indexing.
    - `cmjfront2018` & `cmjfront2026`: Frontend dev servers.

### Jupyter Notebooks
- **Location:** `__notebooks/` and `__notebooks_private/`.
- **Usage:** Heavily used for data migration, analysis, prototyping, and one-off scripts.
- **Pattern:** Use `django_setup.py` in notebooks to initialize the Django environment.

## Configuration & Settings

- **Modular Settings:** Settings are NOT in a single `settings.py`. They are split into modules in `cmj/settings/`:
    - `project.py`: Main entry point, imports others.
    - `apps.py`: `INSTALLED_APPS` definition.
    - `drf.py`: Django Rest Framework settings.
- **Environment Variables:** Uses `python-decouple`. See `security.json` or `.env` (if present) for keys like `SECRET_KEY`, `DEBUG`.

## Key Patterns & Conventions

### Search (Solr)
- **Haystack:** Used for Solr integration (`cmj/haystack.py`).
- **Indexing:** `sapl` content is heavily indexed. Check `search_indexes.py` in apps to understand what data is searchable.

### API
- **DRF:** Django Rest Framework is used (`cmj/api/`, `sapl/api/`).
- **URLs:** `cmj/urls.py` aggregates routes. `sapl` URLs are included via `re_path(r'^sapl/', include(...))`.

### Frontend Integration
- Frontend assets are built from `_frontend/` and collected into `collected_static/`.
- Django templates often serve as the entry point (shell) for Vue apps.

## Critical Files
- `ddev.sh`: Dev environment controller.
- `cmj/settings/project.py`: Main settings aggregator.
- `docker/docker-compose-dev.yaml`: Service definition.
- `cmj/urls.py`: Main URL routing.
