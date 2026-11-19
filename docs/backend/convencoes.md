# Convenções do backend

Exemplos e detalhes das regras resumidas no `CLAUDE.md`. Os trechos seguem o código atual de
`sapl/` e `cmj/`.

## CRUD (`sapl/crud/base.py`)

| Classe | Uso |
| --- | --- |
| `Crud` | Listagem, detalhe, criação, edição e exclusão de um model |
| `CrudAux` | Tabelas auxiliares; exige `base.view_tabelas_auxiliares` e usa `crud/list_tabaux.html` |
| `MasterDetailCrud` | Registros filhos, com a URL baseada no `pk` do pai |

Sem personalização:

```python
from sapl.crud.base import CrudAux

OrigemCrud = CrudAux.build(Origem, "")
StatusTramitacaoCrud = CrudAux.build(StatusTramitacao, "status_tramitacao")
```

Com personalização:

```python
class TramitacaoCrud(MasterDetailCrud):
    model = Tramitacao
    parent_field = "materia"
    help_topic = "tramitacao_relatoria"
    public = [RP_LIST, RP_DETAIL]

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ["data_tramitacao", "status"]
        ordered_list = False
        ordering = ("-data_tramitacao",)

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoForm
```

Atributos usados com frequência: `model`, `help_topic`, `public`, `parent_field`,
`list_field_names`, `ordered_list`, `layout_key`, `model_set`, `list_field_names_set`,
`container_field`. A lista completa está no comentário no início de `sapl/crud/base.py`.

Cuidado: `permission_required` vazio torna a view pública. Por padrão, cada view já exige a
permissão correspondente do model, então só sobrescreva em casos especiais.

### Layouts de formulário e detalhe

`CrispyLayoutFormMixin` lê `<app_label>/layouts.yaml`, resolvido pelos diretórios de template. Na
prática, o arquivo fica em `_templates/v2018/<app_label>/layouts.yaml`. A chave padrão é o nome da
classe do model, e `layout_key` escolhe outra.

```yaml
{% load i18n %}
Loa:
  {% trans 'Dados Gerais' %}:
  - ano:2 receita_corrente_liquida:3 tipo_materia:3 numero_materia:2 ano_materia:2 materia:0
  - parlamentares
```

Cada linha é uma linha da grade de 12 colunas, e `campo:N` define a largura. Campos sem largura
dividem o espaço restante.

## URLs

`get_urls()` gera os nomes `<model>_list`, `<model>_create`, `<model>_detail`, `<model>_update` e
`<model>_delete`. Com o namespace, fica `reverse("sapl.materia:tramitacao_list", kwargs={"pk": pk})`.

```python
from django.urls.conf import include, re_path

from cmj.loa import views

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(
        r"^loa",
        include(
            views.v_loa.LoaCrud.get_urls()
            + views.v_emendaloa.EmendaLoaCrud.get_urls()
        ),
    ),
    re_path(r"^loa/dash", LoaDashboardView.as_view(), name="loa_dashboard"),
]
```

Importe o módulo em `cmj/urls.py` e inclua-o em `urlpatterns_all`, antes de `cmj.sigad.urls`.

## Models

```python
from cmj.mixins import CmjAuditoriaModelMixin, CmjSearchMixin


class Contato(CmjSearchMixin, CmjAuditoriaModelMixin):
    nome = models.CharField(max_length=100)

    @property
    def fields_search(self):
        return ["nome", "nome_social", "apelido"]
```

| Mixin | Fornece |
| --- | --- |
| `CmjModelMixin` | `created`, `modified`, e `clean()` no `save()` (desative com `clean=False`) |
| `CmjAuditoriaModelMixin` | O anterior, mais `owner` e `modifier` |
| `CmjSearchMixin` | Campo `search`, preenchido e normalizado no `save()` |

Itens aceitos em `fields_search`: nome de campo, caminho `rel__campo` e método iniciado por `hook_`.

Para busca por trigramas, declare o índice como em `cmj/loa/models/`:

```python
from django.contrib.postgres.indexes import GinIndex, OpClass


class Meta:
    indexes = [
        GinIndex(OpClass("search", name="gin_trgm_ops"), name="meumodelo_search_gin_trgm"),
    ]
```

## API

`/api/<app_label>/<model>/` é gerado por `ApiViewSetConstrutor`. As rotas ficam em
`sapl/api/urls.py`; `cmj/api/urls.py` está vazio.

```python
from django.apps.registry import apps
from rest_framework.decorators import action

from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

ApiViewSetConstrutor.build_class([apps.get_app_config("arq")])


@customize(Draft)
class _Draft:
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(owner=self.request.user)

    @action(detail=True, methods=["POST"])
    def uploadfiles(self, request, *args, **kwargs):
        ...
```

Módulo novo precisa entrar em `import_modules`, em `cmj/api/views.py` ou `sapl/api/views.py`.

```python
from cmj.api.serializers import CmjSerializerMixin, ModelChoiceObjectRelatedField


class MeuModeloSerializer(CmjSerializerMixin):
    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta(CmjSerializerMixin.Meta):
        model = MeuModelo
```

- `CmjSerializerMixin` acrescenta `link_detail_backend`.
- Os serializers e filtros são procurados nos módulos definidos em `DRFAUTOAPI`
  (`cmj/settings/drf.py`).
- Parâmetros da API: `expand`, `include`, `exclude`, `page`, `page_size` e `o`. A sintaxe está na
  docstring de `DrfAutoApiSerializerMixin`.

## Permissões

Cada regra é uma tupla `(Model, permissões, permissões públicas)`:

```python
rules_arq_group_operador = {
    "group": GROUP_ARQ_OPERADOR,
    "rules": [
        (arq_models.Draft, __base__ + ["view_draft"], set()),
    ],
}
```

- `__base__` reúne os cinco radicais `RP_*`, e `__perms_publicas__` é `{RP_LIST, RP_DETAIL}`.
- Grupos do CMJ: constante em `cmj/globalrules/__init__.py`, regra em
  `cmj/globalrules/map_rules.py` e inclusão em `rules_patterns`.
- Grupos do SAPL: `sapl/rules/__init__.py` e `sapl/rules/map_rules.py`.
- As regras são aplicadas no `post_migrate`, portanto só valem depois de `migrate`.
- Em views fora do CRUD, use `django.contrib.auth.mixins.PermissionRequiredMixin` com a permissão
  completa, como `"materia.add_materialegislativa"`.

## Celery

```python
from cmj.celery import app


@app.task(queue="cq_core", bind=True)
def minha_task(self, pk):
    ...
```

| Fila | Código que a usa |
| --- | --- |
| `cq_arq` | `cmj/arq` |
| `cq_core` | `cmj/core`, `sapl/sessao` e parte de `sapl/base` |
| `cq_videos` | `cmj/videos` |
| `cq_base` | `cmj/loa`, `cmj/search` e parte de `sapl/base` |
| `cq_painelset` | `cmj/painelset` |

Os workers são definidos em `docker/start-dev.sh` e `docker/start.sh`. O beat usa
`DatabaseScheduler`, e a task periódica fixa está em `cmj/celery.py`.

## Solr

Passos para indexar um model novo:

1. Crie a classe `CelerySearchIndex, Indexable` em `cmj/search/search_indexes.py` (ou
   `cmj/arq/search_indexes.py`, para o acervo `cmjarq`).
2. Inclua o model em `MODELS_SOLR_DEFAULT` ou `MODELS_SOLR_CMJARQ`, em `cmj/haystack.py`.
3. Ajuste `EXCLUDED_INDEXES` em `cmj/settings/project.py`, para o índice valer só na conexão certa.

## Testes

```python
import pytest
from django.urls import reverse
from model_mommy import mommy


@pytest.mark.django_db(transaction=False)
def test_incluir_norma(admin_client):
    tipo = mommy.make(TipoNormaJuridica, sigla="T", descricao="Teste")
    response = admin_client.get(reverse("sapl.norma:normajuridica_create"))
    assert response.status_code == 200
```

- Marque o teste com `django_db`, inclusive quando ele não usa o banco diretamente: a fixture
  automática de `conftest.py` consulta `AppConfig`.
- `model_mommy` é o padrão predominante; `model_bakery` aparece em poucos arquivos.
- O Celery roda de forma síncrona nos testes.
- O PostgreSQL do compose precisa estar no ar, com `DATABASE_URL_DEV` diferente de
  `DATABASE_URL_BLOCK`.

## Checklist de app novo

1. Crie `apps.py` com `name = "cmj.<app>"` e `label = "<app>"`.
2. Registre o app em `CMJ_APPS` ou `SAPL_APPS` (`cmj/settings/apps.py`).
3. Escreva `models.py` com os mixins adequados e gere a migration com `makemigrations <app>`.
4. Crie o CRUD em `views.py` e `urls.py` com `app_name = AppConfig.name`.
5. Inclua as URLs em `cmj/urls.py`, antes de `cmj.sigad.urls`.
6. Crie `_templates/v2018/<app>/layouts.yaml`.
7. Registre as permissões no `map_rules.py` correspondente e rode `migrate`.
8. Se houver API, crie o módulo em `cmj/api/` e inclua-o em `import_modules`.
