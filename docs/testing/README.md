# Ambiente de Testes - Documentação

Documentação completa sobre o setup, debug e melhorias do ambiente de testes do projeto.

## 📚 Índice

### [01-conftest-melhorias.md](01-conftest-melhorias.md)
Análise estruturada das melhorias implementadas no `conftest.py`:
- **Status atual**: 6 pontos fortes da configuração
- **Melhorias implementadas**: Logging, limpeza de cache, settings isolados, monitor de signals, dados padrão
- **Launches de debug**: 3 novas configurações no VSCode
- **Recomendações futuras**: 4 ideias para expansão

**Leia quando**: Quer entender o que foi melhorado em `conftest.py`

---

### [02-debug-vscode.md](02-debug-vscode.md)
Guia prático de debug interativo do `conftest.py` no VSCode:
- **Launches explicados**: Passo-a-passo dos 3 launches (`F5` para debugar)
- **Exemplos de debug**: 3 casos reais (template database, cache, signals)
- **Painel Debug**: Como usar Variables, Watch, Debug Console
- **Troubleshooting**: Resoluções rápidas para problemas comuns

**Leia quando**: Quer debugar seu `conftest.py` ou testes

---

### [03-melhorias-futuras.md](03-melhorias-futuras.md)
10 propostas com prioridades para expansão do ambiente de testes:
- **Propostas 1-10**: AppConfig, LOA, Factory, Performance, Solr, Redis, Celery, Cobertura, Auditoria, Permissões
- **Prioridades**: Matrix de prioridade/esforço/ROI
- **Próximos passos**: Roadmap imediato, curto, médio e longo prazo

**Leia quando**: Quer entender o que pode ser feito depois

---

## 🚀 Quick Start

### 1. Debug no VSCode (Novo!)
```bash
# Abra conftest.py
# Coloque breakpoint (clique à esquerda da linha)
# F5 → "Pytest: Debug conftest + testes"
# Para no breakpoint — inspecione variáveis com hover
```

**Launches disponíveis**:
- `Pytest: Debug conftest + testes` — Debugar conftest.py diretamente
- `Pytest: Debug specific test file` — Debugar teste + conftest
- `Pytest: Debug conftest setup/teardown` — Ver ordem de fixtures com `--setup-show`

Leia [02-debug-vscode.md](02-debug-vscode.md) para detalhes.

### 2. Usar as Novas Fixtures
```python
# Em um teste novo:

def test_meu_teste(test_user_data, app):
    """Teste usando fixtures padrão"""
    # test_user_data fornece dados de usuários (admin, staff, regular)
    admin_data = test_user_data['admin']
    
    # app fornece cliente HTTP com suporte a usuário padrão
    response = app.get('/meu-endpoint')
    assert response.status_code == 200
```

**Fixtures novas** (autouse):
- `_clear_cache_between_tests` — Limpa cache após cada teste
- `_configure_test_settings` — Força DummyCache + EmailBackend
- `_cleanup_django_signals` — Monitora signal handlers

**Fixtures úteis** (use quando precisar):
- `test_user_data` — Dados padronizados de usuários

Leia [01-conftest-melhorias.md](01-conftest-melhorias.md#2-limpeza-de-cache-entre-testes) para detalhes.

### 3. Verificar Cobertura de Testes
```bash
# Ver o que está sendo testado
python -m pytest cmj/loa/tests/test_something.py --setup-show -vv

# Com mais detalhes
python -m pytest cmj/loa/tests/ -vv --capture=no
```

---

## 📋 Checklist: Começar a Usar

- [ ] Leia [02-debug-vscode.md](02-debug-vscode.md) (5 min)
- [ ] Teste um launch: F5 em `conftest.py` (10 min)
- [ ] Coloque breakpoint e inspecione variáveis (5 min)
- [ ] Use `test_user_data()` em um novo teste (optional)
- [ ] Compartilhe feedback: quais fixtures precisam?

---

## 🔍 Troubleshooting Rápido

| Problema | Solução | Docs |
|----------|---------|------|
| "Não consigo debugar conftest.py" | Use Launch 1 (`Pytest: Debug conftest + testes`) | [02-debug-vscode.md](02-debug-vscode.md#1️⃣-pytest-debug-conftest--testes) |
| "Cache não está sendo limpo" | Fixture `_clear_cache_between_tests` está rodando | [02-debug-vscode.md](02-debug-vscode.md#exemplo-2-debugar-limpeza-de-cache) |
| "Vejo muitos logs" | Use Launch 3 com `--setup-show` | [02-debug-vscode.md](02-debug-vscode.md#3️⃣-pytest-debug-conftest-setupteardow) |
| "Quero adicionar nova fixture" | Leia [03-melhorias-futuras.md](03-melhorias-futuras.md) para prioridades | [03-melhorias-futuras.md](03-melhorias-futuras.md) |

---

## 📊 Resumo das Mudanças

### Arquivos Modificados
- **conftest.py** ← 6 melhorias implementadas
- **.vscode/launch.json** ← 3 launches de debug adicionados

### Arquivos Criados (Documentação)
- **docs/testing/01-conftest-melhorias.md** — Análise das melhorias
- **docs/testing/02-debug-vscode.md** — Guia prático de debug
- **docs/testing/03-melhorias-futuras.md** — Propostas e roadmap
- **docs/testing/README.md** — Este arquivo

---

## 🔗 Referências

**Projeto**:
- [CLAUDE.md](../../CLAUDE.md) — Instruções gerais do projeto
- [pyproject.toml](../../pyproject.toml) — Configuração de pytest
- [conftest.py](../../conftest.py) — Arquivo de setup de testes

**Externo**:
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Django testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [VSCode Debugging](https://code.visualstudio.com/docs/python/debugging)

---

## 📝 Próximas Revisões

**Próxima revisão**: Após usar um launch de debug em um teste real  
**Contrib**: Reporte feedback em [GitHub Issues](https://github.com/cmj/issues) ou comente em PRs  
**Atualização**: 2026-11-19

---

**Status**: ✅ Documentação completa | ✅ Sem quebras de compatibilidade | ✅ Pronto para usar
