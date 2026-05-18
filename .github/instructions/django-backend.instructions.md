---
description: "Use when writing, editing or reviewing Django views, models, serializers, forms, URLs or CRUD classes in cmj/ or sapl/. Covers Crud base classes, model mixins, DRF serializers and permission patterns."
applyTo: "{cmj,sapl}/**/*.py"
---

# Django Backend Conventions

## CRUD (sapl/crud/base.py)

Prefira as classes base do `sapl/crud/` em vez de views genéricas do Django.

| Classe | Quando usar |
|--------|-------------|
| `Crud` | CRUD padrão (list/detail/create/update/delete) |
| `CrudAux` | Tabelas auxiliares/configuração com permissão relaxada |
| `MasterDetailCrud` | Relação pai-filho (ex: Matéria → Tramitação) |

**Build simples** (sem customização):
```python
from sapl.crud.base import Crud, CrudAux
OrigemCrud = CrudAux.build(Origem, "")
StatusTramitacaoCrud = CrudAux.build(StatusTramitacao, "status_tramitacao")
```

**Com customização de view:**
```python
class AssuntoMateriaCrud(CrudAux):
    model = AssuntoMateria
    class CreateView(CrudAux.CreateView):
        form_class = AssuntoMateriaForm
    class UpdateView(CrudAux.UpdateView):
        form_class = AssuntoMateriaForm
```

**Atributos configuráveis em qualquer CRUD:**
- `model` — modelo associado
- `list_field_names` — campos visíveis na listagem
- `permission_required` — tupla de constantes `RP_*`
- `help_topic` — tópico de ajuda (opcional)

## URLs

URLs do CRUD são geradas via `.get_urls()`. Padrão do arquivo `urls.py`:

```python
app_name = 'materia'

urlpatterns = [
    *MateriaLegislativaCrud.get_urls(),
    *TramitacaoCrud.get_urls(),
    re_path(r'^materia/(?P<pk>\d+)/acao/$', MinhaView.as_view(), name='acao'),
]
```

Registrar o `urls.py` do app em `cmj/urls.py` (CMJ) ou no `urls.py` do sapl.

## Models

Herdar os mixins conforme necessidade:

```python
from cmj.mixins import CmjAuditoriaModelMixin, CmjSearchMixin

class MeuModelo(CmjSearchMixin, CmjAuditoriaModelMixin, models.Model):
    # CmjAuditoriaModelMixin adiciona: owner, modifier (FK User), data_criacao, data_atualizacao
    # CmjSearchMixin adiciona: search (TextField), populado automaticamente no save()
    nome = models.CharField(max_length=255)

    class Meta:
        ordering = ['-data_criacao']
```

**`CmjAuditoriaModelMixin`** — rastreamento de autoria (owner/modifier/datas).

**`CmjSearchMixin`** — busca full-text **no PostgreSQL** via trigrama (não é Solr). O `save()` do mixin popula o campo `search` chamando os métodos listados em `fields_search`. Requer:

1. Implementar `fields_search` retornando lista de nomes de métodos a chamar:
```python
@property
def fields_search(self):
    return ["hook_search"]   # o save() chamará self.hook_search()

def hook_search(self):
    # retorna string com todo o conteúdo pesquisável
    return f"{self.nome} {self.historico}"
```

2. Declarar `GinIndex` com `gin_trgm_ops` em `Meta.indexes`:
```python
from django.contrib.postgres.indexes import GinIndex, OpClass

class Meta:
    indexes = [
        GinIndex(
            OpClass("search", name="gin_trgm_ops"),
            name="meumodelo_search_gin_trgm",
        ),
    ]
```

## Serializers (DRF)

```python
from cmj.api.serializers import CmjSerializerMixin
from rest_framework import serializers

class MeuModeloSerializer(CmjSerializerMixin):
    # CmjSerializerMixin adiciona link_detail_backend automaticamente
    campo_calculado = serializers.SerializerMethodField()

    class Meta:
        model = MeuModelo
        fields = '__all__'  # ou lista explícita; use exclude para omitir campos pesados

    def get_campo_calculado(self, obj):
        return obj.algum_calculo()
```

Para retornar FK como objeto completo (em vez de só id):
```python
from drfautoapi.drfautoapi import ModelChoiceObjectRelatedField
campo_fk = ModelChoiceObjectRelatedField(read_only=True)
```

## Permissões

```python
from sapl.rules import RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE
# Constantes expandidas para: '{app_label}.list_{model}', etc.

class MinhaView(PermissionRequiredMixin, View):
    permission_required = ('materia.add_materialegislativa',)
```

Em CRUDs, a permissão é inferida automaticamente do modelo. Só sobrescreva `permission_required` para regras especiais.

Novos grupos de permissão: registrar em `cmj/globalrules/map_rules.py` (apps CMJ) ou `sapl/rules/apps.py` (apps SAPL).

## Checklist — novo app Django

1. `models.py` — herdar `CmjAuditoriaModelMixin`; definir `Meta.ordering`
2. `views.py` — usar `Crud.build()` ou classe herdando `Crud`
3. `urls.py` — `app_name`, `urlpatterns` com `.get_urls()`
4. `forms.py` — crispy-forms (`FormHelper`, `Layout`)
5. `apps.py` — `AppConfig` com `name` e `label`
6. Adicionar em `INSTALLED_APPS` → `cmj/settings/apps.py`
7. Templates em `templates/{app_label}/`
8. Registrar permissões em `globalrules/map_rules.py` ou `sapl/rules/`
