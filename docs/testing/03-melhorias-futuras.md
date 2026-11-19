# Melhorias Futuras do Ambiente de Testes

## 📊 Status: Implementadas vs. Propostas

### ✅ Implementadas Nesta Sessão

| Melhoria | Escopo | Impacto |
|----------|--------|--------|
| Logging no conftest | Setup/Teardown | Alto — Debug fácil |
| Limpeza de cache | Between testes | Alto — Sem estado cruzado |
| Settings isolados | Session | Médio — Garantia de isolamento |
| Monitor de signals | Function | Baixo — Diagnóstico apenas |
| Dados padrão | Session | Baixo — Referência para novos testes |
| VSCode launches × 3 | Dev | Alto — Debug interativo |

### 🚀 Propostas (Sem Implementar)

Essas melhorias têm valor mas precisam de decisão antes de implementar.

---

## 1. Fixture para AppConfig Padrão Expandida

**O quê**: Criar registros default de AppConfig com modo, permissões, etc.

**Por quê**: 
- Atualmente, `create_base_appconfig()` cria só o ID
- Testes que checam permissões precisam de House.modo, Area.tipo, etc.

**Como implementar**:
```python
@pytest.fixture(scope="session")
def default_appconfig(django_db):
    """Cria AppConfig com defaults para testes"""
    from sapl.base.models import AppConfig
    
    config = AppConfig.objects.first()
    config.modo_painel = 'legislativo'
    config.save()
    return config
```

**Risco**: 
- Pode ficar muito grande se replicar toda produção
- Melhor: Mínimo viável para cada app

**Recomendação**: Implementar conforme novos testes peçam.

---

## 2. Fixture para Dados de LOA

**O quê**: Criar estrutura padrão de LOA (Orçamento, Fases, Emendas, etc.)

**Por quê**: 
- Leia antes: `docs/specs/loa/fases-emenda.md` (você pediu para gerar)
- Muitos testes de LOA precisam de dados base

**Exemplo**:
```python
@pytest.fixture(scope="session")
def loa_test_data(django_db, admin_user):
    """Cria Orçamento, Áreas, Fases para testes de LOA"""
    # Leia a spec ANTES
    # Crie: Orçamento 2024, Áreas, permissões
```

**Recomendação**: 
- Esperar até ter spec de LOA finalizada
- Implementar como complemento da spec

---

## 3. Factory Pattern para Modelos

**O quê**: Usar `factory_boy` para gerar modelos em vez de fixture (como algumas projetos fazem)

**Comparação**:

| Aspecto | Fixture Session | Factory |
|--------|-----------------|---------|
| Reutilização | ✅ Uma vez/session | ❌ Rebuilds cada teste |
| Performance | ✅ Rápido | ❌ Lento |
| Flexibilidade | ⚠️ Limitada | ✅ Customizável |
| Legibilidade | ⚠️ Implícito | ✅ Explícito |

**Recomendação**: Manter fixtures session. Factories só se muito boilerplate.

---

## 4. Monitoramento de Performance

**O quê**: Adicionar hook `pytest_runtest_setup` para alertar se setup > 1s

**Por quê**: 
- Algumas fixtures PostgreSQL são lentas
- Detectar degradação cedo

**Código**:
```python
import pytest
import time

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    item.setup_start = time.time()

@pytest.hookimpl(trylast=True)
def pytest_runtest_setup_finish(item):
    elapsed = time.time() - item.setup_start
    if elapsed > 1.0:
        logger.warning(f"Setup lento ({elapsed:.2f}s): {item.name}")
```

**Recomendação**: Implementar se testes forem lentos em CI.

---

## 5. Fixture para Solr / Busca

**O quê**: Limpar/resetar índice Solr antes de cada teste

**Por quê**: 
- `USE_SOLR=True` em produção, mas não em testes
- Testes que usam busca precisam de índice limpo

**Código**:
```python
@pytest.fixture(autouse=True)
def _reset_solr_index(settings):
    """Limpa índice Solr antes de cada teste"""
    if not settings.USE_SOLR:
        yield
        return
    
    from haystack import connections
    
    conn = connections['default']
    conn.clear()
    yield
    conn.clear()
```

**Recomendação**: Implementar se testes de busca falharem.

---

## 6. Fixture para Cache Redis

**O quê**: Testar com Redis real (além de DummyCache)

**Por quê**: 
- Atualmente, testes com DummyCache (nenhuma cache)
- Redis pode falhar de formas diferentes (timeout, eviction)
- Produção usa Redis

**Escopo**: Testar com 2 backends:
1. `DummyCache` (rápido, default)
2. `LocMemCache` (simula Redis localmente)

**Código**:
```python
@pytest.fixture(params=['dummy', 'locmem'])
def cache_backend(request, settings):
    """Parametriza testes com diferentes backends de cache"""
    if request.param == 'dummy':
        settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
    else:
        settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    
    yield request.param
```

**Recomendação**: Implementar se testes com cache falharem esporadicamente.

---

## 7. Fixture para Mock de Celery Task

**O quê**: Interceptar tasks Celery para debug

**Por quê**: 
- Atualmente, `task_always_eager=True` executa sync
- Às vezes, precisa de logs/rastreamento de task
- Ou replicar falha de task (timeout, retry)

**Código**:
```python
@pytest.fixture
def mock_celery_task(monkeypatch):
    """Intercepta task Celery para debug"""
    tasks_called = []
    
    original_apply_async = None
    
    def track_task(self, *args, **kwargs):
        tasks_called.append({
            'name': self.name,
            'args': args,
            'kwargs': kwargs,
        })
        # Ainda executa sincronamente
        return self.apply_async(*args, **kwargs)
    
    # monkeypatch celery.Task
    tasks_called.clear()
    return tasks_called
```

**Recomendação**: Implementar se tasks forem problema em testes.

---

## 8. Relatório de Cobertura por App

**O quê**: Adicionar `pytest-cov` com relatório por app

**Por quê**: 
- Saber qual app tem menos testes
- Priorizar testes críticos

**Configuração em `pyproject.toml`**:
```toml
[tool.coverage.run]
source = ["cmj", "sapl", "drfautoapi"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

**Comando**:
```bash
python -m pytest --cov=cmj --cov=sapl --cov-report=html
# Abre htmlcov/index.html
```

**Recomendação**: Implementar antes de release para medir qualidade.

---

## 9. Fixture para Auditoria

**O quê**: Capturar e verificar eventos de auditoria em testes

**Por quê**: 
- CLAUDE.md menciona `CmjAuditoriaModelMixin` que registra `owner`, `modifier`
- Testes podem verificar auditoria automaticamente

**Código**:
```python
@pytest.fixture
def audit_log(django_db):
    """Captura eventos de auditoria durante teste"""
    from cmj.core.models import AuditoriaLog  # (fictício)
    
    initial_count = AuditoriaLog.objects.count()
    
    yield lambda: AuditoriaLog.objects.all()[initial_count:]
    
    # Teardown: limp opcional
```

**Recomendação**: Implementar se precisar de testes de auditoria.

---

## 10. Fixture para Permissões

**O quê**: Setup automático de permissões padrão por grupo

**Por quê**: 
- Muitos testes precisam de permissões (RP_LIST, RP_DETAIL, etc.)
- Permissões são criadas em `post_migrate`, mas testes `--no-migrations`

**Código**:
```python
@pytest.fixture(scope="session")
def default_permissions(django_db):
    """Cria grupos e permissões para testes"""
    from cmj.globalrules.models import RoleGroup
    
    # Leia: cmj/globalrules/map_rules.py
    # Implemente mapeamento padrão
```

**Recomendação**: Implementar conforme testes precisarem de permissões.

---

## 🎯 Prioridade de Implementação

| Item | Prioridade | Esforço | ROI |
|------|-----------|--------|-----|
| **Já feito** (logging, cache, signals) | 🔴 Done | 2h | Alto |
| AppConfig expandida | 🟡 Média | 1h | Médio |
| Dados de LOA | 🟢 Baixa | 2h | Alto (pré-spec) |
| Solr fixture | 🟢 Baixa | 1h | Baixo (se usar buscas) |
| Cobertura + relatório | 🟡 Média | 1h | Médio |
| Auditoria fixture | 🟢 Baixa | 1h | Baixo (pré-testes) |
| Performance monitoring | 🟡 Média | 2h | Médio (pré-CI) |
| Permissões fixture | 🟡 Média | 2h | Alto (bloqueia testes) |

---

## 📝 Próximos Passos

### Imediato
1. ✅ Testar os 3 launches de debug no VSCode
2. ✅ Colocar breakpoint em conftest.py e confirmar que para
3. ✅ Usar `--setup-show` em um teste para ver fixture order

### Curto Prazo (Próximas 2 semanas)
1. Leia `docs/specs/loa/fases-emenda.md` (você já pediu spec)
2. Se testes falharem por permissões → Implementar fixture de permissões
3. Se testes forem lentos → Implementar monitoramento de performance

### Médio Prazo (Próximo sprint)
1. Adicionar `pytest-cov` e medir cobertura por app
2. Expandir `default_appconfig` conforme novos apps precisem
3. Implementar fixture de dados de LOA após spec

### Longo Prazo (Before Release)
1. Relatório final de cobertura por app
2. Documentar quais fixtures usar para cada tipo de teste
3. Treinar time em debug interativo (VSCode launches)

---

## 🔗 Referências

- **pytest fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **Django testing**: https://docs.djangoproject.com/en/stable/topics/testing/
- **pytest-django**: https://pytest-django.readthedocs.io/
- **Cobertura**: https://coverage.readthedocs.io/

---

**Proposta criada**: 2026-11-19
**Baseada em**: CLAUDE.md, conftest.py atual, pyproject.toml
**Próxima revisão**: Após implementar 2-3 itens acima
