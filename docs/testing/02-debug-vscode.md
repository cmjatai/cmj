# Guia Prático: Debug do conftest.py no VSCode

## 🎯 Objetivo
Permitir debug interativo do `conftest.py` para diagnosticar problemas de setup/teardown de testes.

## ⚙️ Launches Configurados em `.vscode/launch.json`

### 1️⃣ "Pytest: Debug conftest + testes"
**Melhor para**: Debugar fixtures específicas do conftest

**Passos**:
```
1. Abra conftest.py no VSCode
2. Coloque breakpoint (clique na linha, à esquerda do número)
   Exemplo: linha 20 em create_base_appconfig
3. Pressione F5
4. Selecione "Pytest: Debug conftest + testes"
5. Execução para no breakpoint
6. Use painel Debug para:
   - Ver variáveis locais (request, django_db_blocker, etc.)
   - Step over (F10) ou step into (F11)
   - Mudar valores em tempo real
```

**Variáveis úteis para inspecionar**:
- `request`: Objeto pytest.FixtureRequest com dados do teste
- `django_db_setup`: Parâmetros de banco (host, port, user)
- `settings`: Django settings (DATABASES, CACHES)
- `psycopg`: Conexão com PostgreSQL

---

### 2️⃣ "Pytest: Debug specific test file"
**Melhor para**: Debugar interação entre conftest + arquivo de teste

**Passos**:
```
1. Abra um arquivo de teste: cmj/loa/tests/test_something.py
2. Coloque breakpoint no seu teste
3. F5 → "Pytest: Debug specific test file"
4. Se pedir args, deixe em branco (usa arquivo atual)
5. Vê setup de fixtures + seu teste + teardown
```

**Flags automáticas**:
- `-vv`: Output verboso (nome do teste, fixtures usadas)
- `--tb=short`: Traceback conciso
- `--capture=no`: Print/logging aparecem em tempo real (não bufferizados)

---

### 3️⃣ "Pytest: Debug conftest setup/teardown"
**Melhor para**: Entender ordem de execução e escopos de fixtures

**Passos**:
```
1. Abra conftest.py ou um teste
2. F5 → "Pytest: Debug conftest setup/teardown"
3. Console mostra:
   
   SETUP    django_db (scope=session)
   SETUP    _clear_cache_between_tests (scope=function)
   SETUP    _configure_test_settings (scope=session)
   TEST     test_meu_teste
   TEARDOWN _clear_cache_between_tests
   TEARDOWN django_db
```

**Por que `--setup-show` ajuda**:
- Vê qual fixture levou mais tempo (slow setup)
- Identifica ordem errada (escopos misturados)
- Encontra fixtures não usadas

---

## 🐛 Exemplos de Debug

### Exemplo 1: Debugar criação do template database
**Problema**: Template database não está sendo criado com extensões

```python
# conftest.py, linha 76 (fixture django_db_setup)
# 1. Coloque breakpoint aqui:

tpl_conn = psycopg.connect(**conn_params)  # ← breakpoint

# 2. F5 → Launch 1
# 3. Quando para:
#    - Hover sobre conn_params para ver (host, port, dbname)
#    - Execute no Debug Console: psycopg.__version__
#    - Veja se conexão está aberta
```

### Exemplo 2: Debugar limpeza de cache
**Problema**: Cache não está sendo limpo entre testes

```python
# conftest.py, linha 130 (_clear_cache_between_tests)
# 1. Coloque breakpoint:

if hasattr(cache, 'clear'):
    cache.clear()  # ← aqui

# 2. F5 → Launch 1
# 3. Debug Console:
#    - cache (vê tipo: DummyCache, MemoryCache, etc.)
#    - cache._cache (inspeciona conteúdo)
#    - cache.__class__.__name__
```

### Exemplo 3: Debugar signal handlers
**Problema**: Muitos handlers de signal acumulando

```python
# conftest.py, linha 158 (_cleanup_django_signals)
# 1. Coloque breakpoint:

for signal in [signals.post_save, signals.post_delete, signals.pre_save]:
    logger.debug(...)  # ← breakpoint aqui

# 2. F5 → Launch 1
# 3. Debug Console:
#    - len(signal.receivers) (quantos handlers)
#    - signal.receivers (lista de handlers)
```

---

## 📋 Painel Debug do VSCode

Quando está em breakpoint, você tem acesso a:

| Painel | O quê |
|--------|-------|
| **Variables** | Variáveis locais, globals, closure |
| **Watch** | Expressões customizadas (e.g., `len(signal.receivers)`) |
| **Call Stack** | Stack trace (clica em frame para ver código) |
| **Breakpoints** | Lista e toggle de breakpoints |
| **Debug Console** | Executa Python ao vivo (comando interativo) |

**Debug Console - Comandos úteis**:
```python
# Ver variável
> cache
<DummyCache ...>

# Executar método
> cache.clear()

# Importar e inspecionar
> from django.conf import settings
> settings.DATABASES['default']
{...}

# Verificar fixture
> hasattr(request, 'getfixturevalue')
True
```

---

## 🔧 Troubleshooting

### "Não consigo colocar breakpoint no conftest.py"
- ✅ Clique à esquerda do número da linha (ponto vermelho aparece)
- ✅ Certifique que o pytest é executado (não `python conftest.py`)
- ✅ Coloque breakpoint ANTES de F5 (ordem importa)

### "Debug para em outro arquivo, não no conftest"
- ✅ Launch está correto, mas deve-se abrir `conftest.py` primeiro
- ✅ Se abrir teste, vai parar no teste também — use "Debug conftest setup/teardown"

### "Vejo muitos logs, não dá para achar meu breakpoint"
- ✅ Use Launch 3 (`--setup-show`) para ver estrutura
- ✅ Coloque breakpoint numa linha específica (não função toda)
- ✅ Debug Console: `request.node.name` para ver teste atual

### "Cache não está sendo limpo"
- ✅ Verifique se fixture `_clear_cache_between_tests` está rodar (Launch 3)
- ✅ Veja tipo de cache: `> type(cache).__name__`
- ✅ Se for MemoryCache, confirme `hasattr(cache, 'clear')`

---

## 💡 Dicas Avançadas

### 1. Debug condicional (só algumas iterações)
```python
# No seu código, em vez de sempre parar:
def _clear_cache_between_tests():
    from django.core.cache import cache
    
    # Coloque condicional manual:
    import sys
    if 'test_loa' in sys.argv:  # Debugar só testes de LOA
        breakpoint()  # Python built-in
    
    cache.clear()
```

### 2. Monitorar variável em Watch
```
Na aba Watch (+):
- len(signal.receivers)
- cache.__class__.__name__
- settings.DATABASES['default']['HOST']
```

### 3. Usar Debug Console para testar
```
Enquanto parado em breakpoint:
> from cmj.settings import settings
> settings.CACHES['default']
{'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
```

---

## 🚀 Fluxo Recomendado para Debugar conftest

1. **Identifique o problema**:
   - Teste falha com erro de setup? → Debugar `django_db_setup`
   - Teste anterior afeta o próximo? → Debugar `_clear_cache_between_tests`
   - Signal handlers não limpos? → Debugar `_cleanup_django_signals`

2. **Coloque breakpoint** na fixture relevante

3. **Escolha launch**:
   - Só conftest? → Launch 1
   - Conftest + meu teste? → Launch 2
   - Entender ordem? → Launch 3

4. **F5** e inspecione variáveis

5. **Step over/into** para ver execução passo-a-passo

6. **Debug Console** para testar expressões

---

**Última atualização**: 2026-11-19
**Referências**: `.vscode/launch.json`, pytest docs
