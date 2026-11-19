# Análise e Melhorias do conftest.py

## Status Atual ✅

A configuração atual de testes é bem estruturada e cobre os pontos críticos:

### Pontos Fortes
1. **Setup robusto de banco**: Cria template database com extensões PostgreSQL (pgvector, pg_trgm, unaccent)
2. **Isolamento seguro**: Usa `django_db_blocker` para operações de banco
3. **Celery sincronizado**: Executa tasks sem Redis/broker
4. **Fixture bem nomeada**: `create_base_appconfig` evita erros de importação
5. **WebTest integrado**: `OurTestApp` facilita testes HTTP
6. **Configuração limpa**: Respeita flags como `--no-migrations` e `--reuse-db`

## Melhorias Implementadas 🚀

### 1. Logging Estratégico
- **O quê**: Adicionado `logging` para debug de setup/teardown
- **Por quê**: Facilita diagnóstico quando testes falham no CI ou em máquinas diferentes
- **Como**: Log de warnings em exceções de teardown

### 2. Limpeza de Cache Entre Testes
```python
@pytest.fixture(autouse=True)
def _clear_cache_between_tests():
    """Limpa cache após cada teste"""
```
- **O quê**: Fixture autouse que limpa Django cache após cada teste
- **Por quê**: DummyCache em DEBUG não persiste, mas melhor garantir estado limpo
- **Quando usar**: Sempre ativo para testes que usam cache (e.g., permissões, dados)

### 3. Configuração de Settings para Testes
```python
@pytest.fixture(scope="session", autouse=True)
def _configure_test_settings():
    """Define settings específicos para testes"""
```
- **O quê**: Força `DummyCache` e `EmailBackend` em memória
- **Por quê**: Evita efeitos colaterais (emails reais, cache persistente)
- **Escopo**: Session (roda uma vez por bateria de testes)

### 4. Limpeza de Signal Handlers
```python
@pytest.fixture(autouse=True)
def _cleanup_django_signals():
    """Monitora signal handlers entre testes"""
```
- **O quê**: Log de debug para verificar handlers de sinais
- **Por quê**: CLAUDE.md menciona que signals globais (auditoria, rede social) escutam `post_save` em todos models
- **Como**: Registra quantos receivers estão ativos (diagnóstico, não desconecta para manter handlers app)

### 5. Dados Padrão de Teste
```python
@pytest.fixture(scope="session")
def test_user_data():
    """Define estrutura padrão de usuários de teste"""
```
- **O quê**: Fornece dados padronizados para criar usuários em testes
- **Por quê**: Evita duplicação e garante consistência (passwords, emails)
- **Uso**: `def test_something(test_user_data): user_data = test_user_data['admin']`

### 6. Documentação Melhorada
- Adicionados docstrings a `OurTestApp`
- Comments explicativos em cada fixture

## Configurações de Debug no VSCode 🔍

### Launch: "Pytest: Debug conftest + testes"
Roda o arquivo atual com pytest e debugger ativo. Ideal para:
- Colocar breakpoint em `conftest.py` e ver execução de setup
- Debug de fixtures que falharam
- Verificar ordem de execução

**Como usar**:
1. Abra `conftest.py` (ou um arquivo de teste)
2. Pressione F5, selecione "Pytest: Debug conftest + testes"
3. Coloque breakpoint na fixture que quer debugar
4. Run — o pytest vai parar no seu breakpoint

### Launch: "Pytest: Debug specific test file"
Roda um arquivo de teste específico com flags `-vv` e `--capture=no`:
- Vê saída completa de print/logging durante debug
- Traceback detalhado

**Como usar**:
1. Abra um arquivo de teste (e.g., `cmj/loa/tests/test_something.py`)
2. F5 → "Pytest: Debug specific test file"
3. Se pediu args, coloque caminho do teste ou deixe vazio para arquivo atual

### Launch: "Pytest: Debug conftest setup/teardown"
Exibe setup/teardown de cada teste com `--setup-show`:
- Vê exatamente qual fixture está rodando antes/depois de cada teste
- Debugar problemas de fixture scope

**Exemplo de saída**:
```
test_session.py::test_something (fixtures used: django_db, app)
  SETUP    django_db (scope=session)
  SETUP    _clear_cache_between_tests (scope=function) ← aqui você pode colocar breakpoint
  TEST     test_something
  TEARDOWN _clear_cache_between_tests
  TEARDOWN django_db
```

## Recomendações Futuras 💡

### 1. Fixture para Dados de Teste Comuns
Se muitos testes precisarem de dados padrão, criar:
```python
@pytest.fixture
def default_test_data(django_db, admin_user):
    """Cria Usuário, Área de trabalho, Permissões padrão"""
    # Leia antes de implementar: docs/specs/loa/fases-emenda.md
```

### 2. Monitoramento de Performance
Adicionar hook `pytest_runtest_setup` para alertar se fixtures levam > 1s

### 3. Fixture para Solr (Busca)
Se testes usam `USE_SOLR=True`, fixture para:
- Limpar índice antes de cada teste
- Ou usar mock de SearchQuerySet

### 4. Fixture para Cache Redis
Atualmente testa com DummyCache. Considerar:
- Testar com Redis de verdade em CI
- Fixture para simular timeout de Redis

## Checklist para Usar as Melhorias ✓

- [x] Logging adicionado — agora `conftest.py` gera logs úteis
- [x] Cache limpo entre testes — sem vazamento de estado
- [x] Settings de teste centralizados — fácil de mudar
- [x] Signal handlers monitorados — Debug via log
- [x] Dados padrão estruturados — Use em novos testes
- [x] VSCode launches configurados — F5 para debugar fixtures

## Teste as Configurações

```bash
# Debug conftest.py com VSCode
# 1. Abra conftest.py no VSCode
# 2. Coloque breakpoint em uma fixture (linha 20, dentro de create_base_appconfig)
# 3. F5 → "Pytest: Debug conftest + testes"
# 4. Vai parar no breakpoint

# Ou roda testes sem VSCode para ver logs
python -m pytest cmj/loa/tests/test_something.py -vv --capture=no

# Com --setup-show vê ordem de execução (útil sem debugger)
python -m pytest cmj/loa/tests/test_something.py --setup-show -vv
```

---

**Documento criado**: 2026-11-19
**Referências**: CLAUDE.md, conftest.py, pyproject.toml
