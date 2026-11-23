import importlib
import inspect
import logging
import re
from collections import OrderedDict
from functools import cached_property

import django_filters
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models.base import ModelBase
from django.db.models.fields import CharField, TextField
from django.db.models.fields.files import FileField
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ManyToManyField
from django.template.defaultfilters import capfirst
from django.urls.conf import path
from django.utils.translation import gettext_lazy as _
from django_filters.constants import ALL_FIELDS, EMPTY_VALUES
from django_filters.fields import ModelMultipleChoiceField
from django_filters.filters import CharFilter
from django_filters.filterset import FilterSet
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.utils import get_all_model_fields, resolve_field
from rest_framework import serializers as rest_serializers
from rest_framework.relations import ManyRelatedField
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class SplitStringCharFilter(django_filters.CharFilter):
    _re = re.compile(r'("[^"]+"| +|[^"]+)')

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        lookup = "%s__%s" % (self.field_name, self.lookup_expr)

        values = [value]
        if self.lookup_expr == "icontains":
            if not '"' in value:
                values = value.split(" ")
            else:
                values = list(
                    filter(
                        lambda x: x and x != " " and x[0] != '"',
                        self._re.findall(value),
                    )
                ) + list(
                    map(
                        lambda x: x[1:-1],
                        filter(lambda x: x and x[0] == '"', self._re.findall(value)),
                    )
                )

        if not isinstance(values, list):
            values = [values]
        for v in values:
            qs = self.get_method(qs)(**{lookup: v})
        return qs


class M2MFilter(django_filters.ModelMultipleChoiceFilter):

    class M2MFieldFormField(ModelMultipleChoiceField):
        def clean(self, value):
            if value in EMPTY_VALUES:
                return super().clean(value)
            values = list(map(lambda x: x.replace(" ", "").split(","), value))
            values = [v for subvalues in values for v in subvalues]
            cleaned_values = tuple(super().clean(values))
            return (cleaned_values,) if cleaned_values else cleaned_values

    field_class = M2MFieldFormField
    distinct = True


class ApiFilterSetMixin(FilterSet):

    o = CharFilter(method="filter_o")
    id__in = CharFilter(method="filter_id__in")

    class Meta:
        fields = "__all__"
        filter_overrides = {
            FileField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {
                    "lookup_expr": "exact",
                },
            },
            CharField: {
                "filter_class": SplitStringCharFilter,
            },
            TextField: {
                "filter_class": SplitStringCharFilter,
            },
            JSONField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {
                    "lookup_expr": "exact",
                },
            },
        }

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        self.base_filters = self.filters_named_in(data, prefix)
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.drop_filters_of_unreadable_fields()

    def filters_named_in(self, data, prefix=None):
        """Só os filtros que a requisição cita são instanciados, mais os
        declarados à mão: copiar e montar todos os filtros gerados do model a
        cada requisição custa dezenas de milissegundos. A classe continua com
        todos em ``base_filters``, de onde o esquema os lê."""
        base_filters = type(self).base_filters
        if prefix:
            return base_filters
        named = set(data or ())
        return OrderedDict(
            (name, f)
            for name, f in base_filters.items()
            if name in named or name in self.declared_filters
        )

    def drop_filters_of_unreadable_fields(self):
        """Um filtro gerado só vale para campo que o serializer da rota entrega
        ao usuário da requisição. Os demais saem do filterset e o parâmetro é
        ignorado, como qualquer parâmetro desconhecido. Filtros declarados à
        mão num filterset próprio não passam por esta conferência."""
        used = [
            name
            for name in self.filters
            if name in self.data and name not in self.declared_filters
        ]
        if not used:
            return

        view = request_view(self.request)
        if view is None:
            # uso do filterset fora de uma requisição da API
            return

        readable = readable_field_names(view, self.request)
        for name in used:
            if self.filters[name].field_name not in readable:
                del self.filters[name]

    def filter_id__in(self, queryset, name, value):
        try:
            ids = list(map(lambda x: int(x.strip()), value.split(",")))
            return queryset.filter(id__in=ids)
        except:
            return queryset

    def filter_o(self, queryset, name, value):
        try:
            ordering = allowed_ordering(self, value)
            return queryset.order_by(*ordering) if ordering else queryset
        except:
            return queryset

    @classmethod
    def get_fields(cls):
        model = cls._meta.model
        fields_model = get_all_model_fields(model)
        fields_filter = cls._meta.fields
        exclude = cls._meta.exclude

        if exclude is not None and fields_filter is None:
            fields_filter = ALL_FIELDS

        fields = fields_filter if isinstance(fields_filter, dict) else {}

        for f_str in fields_model:
            if f_str not in fields:

                f = model._meta.get_field(f_str)

                if f.many_to_many:
                    fields[f_str] = ["exact", "in"]
                    continue

                fields[f_str] = ["exact"]

                def get_keys_lookups(cl, sub_f):
                    r = []
                    for lk, lv in cl.items():

                        if lk in (
                            "contained_by",
                            "trigram_similar",
                            "unaccent",
                            "search",
                            # sem filtro por expressão regular vinda do
                            # cliente: o valor iria ao banco como está
                            "regex",
                            "iregex",
                        ):
                            continue

                        sflk = f'{sub_f}{"__" if sub_f else ""}{lk}'
                        r.append(sflk)

                        if hasattr(lv, "get_lookups"):
                            r += get_keys_lookups(lv.get_lookups(), sflk)

                        if hasattr(lv, "output_field"):
                            if hasattr(lv.output_field, "get_lookups"):
                                r.append(f'{sflk}{"__" if sflk else ""}range')

                                r += get_keys_lookups(
                                    lv.output_field.class_lookups, sflk
                                )

                    return r

                fields[f_str] = list(
                    set(fields[f_str] + get_keys_lookups(f.get_lookups(), ""))
                )

        # Remove excluded fields
        exclude = exclude or []

        fields = [(f, lookups) for f, lookups in fields.items() if f not in exclude]

        return OrderedDict(fields)

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr="exact"):
        # Redefine método estático para ignorar filtro para
        # fields que não possuam lookup_expr informado
        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            "field_name": name,
            "label": capfirst(f.verbose_name),
            "lookup_expr": lookup_expr,
        }

        filter_class, params = cls.filter_for_lookup(f, lookup_type)
        default.update(params)
        if filter_class is not None:
            return filter_class(**default)
        return None

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):
        f, p = super().filter_for_lookup(field, lookup_type)

        if lookup_type == "in" and isinstance(field, ManyToManyField):
            return M2MFilter, p
        return f, p


class BusinessRulesNotImplementedMixin:
    http_method_names = ["get", "head", "options", "trace"]

    def create(self, request, *args, **kwargs):
        raise Exception(_("POST Create não implementado"))

    def update(self, request, *args, **kwargs):
        raise Exception(_("PUT and PATCH não implementado"))

    def delete(self, request, *args, **kwargs):
        raise Exception(_("DELETE Delete não implementado"))


class DrfautoapiRouter(DefaultRouter):

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = super(DefaultRouter, self).get_urls()

        if self.include_root_view:
            view = self.get_api_root_view(api_urls=urls)
            root_url = path("", view, name=self.root_view_name)
            urls.append(root_url)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls, allowed=["[a-zA-Z.0-9]+"])

        return urls


class ApiViewSetConstrutor:

    _built_sets = {}

    class ApiViewSet(ModelViewSet):
        filter_backends = (DjangoFilterBackend,)

    class LastModifiedDecorator(object):
        def __init__(self):
            pass

        def __call__(self, cls):
            return cls

    @classmethod
    def last_modified_class(cls, klass):
        cls.LastModifiedDecorator = klass
        return cls

    @classmethod
    def get_viewset_for_model(cls, model):
        return cls._built_sets[model._meta.app_config][model]

    @classmethod
    def restricts_queryset(cls, model):
        """O viewset do model restringe os registros que entrega: tem
        ``get_queryset`` próprio ou ``queryset`` filtrado."""
        viewset = cls.get_viewset_for_model(model)
        overrides = viewset.get_queryset is not ModelViewSet.get_queryset
        return overrides or bool(viewset.queryset.query.where)

    @classmethod
    def update(cls, other):
        cls._built_sets.update(other._built_sets)

    @classmethod
    def import_modules(cls, modules):
        for m in modules:
            importlib.import_module(m)

    @classmethod
    def router(cls, router_class=DrfautoapiRouter):
        router = router_class()
        for app, built_sets in cls._built_sets.items():
            for model, viewset in built_sets.items():
                router.register(
                    f"{app.label}/{model._meta.model_name}",
                    viewset,
                    basename=f"{app.label}_{model._meta.model_name}",
                )
        return router

    @staticmethod
    def import_configured_module(name):
        """Importa um módulo configurado de serializers ou de filtersets.

        A geração não segue sem ele: se o módulo não importa, ou ainda está
        sendo importado (importação circular, que deixaria de fora as classes
        definidas depois deste ponto), a configuração é inválida.
        """
        name = name.strip()
        try:
            module = importlib.import_module(name)
        except Exception as e:
            raise ImproperlyConfigured(
                f"drfautoapi: o módulo configurado '{name}' não pôde ser importado: {e}"
            ) from e
        if getattr(getattr(module, "__spec__", None), "_initializing", False):
            raise ImproperlyConfigured(
                f"drfautoapi: o módulo configurado '{name}' ainda está sendo "
                "importado. Ele não pode importar, direta ou indiretamente, um "
                "módulo que chama build_class."
            )
        return module

    @classmethod
    def import_configured_class(cls, dotted_path):
        """Importa uma classe configurada pelo caminho ``modulo.Classe``."""
        module_name, _sep, class_name = dotted_path.strip().rpartition(".")
        module = cls.import_configured_module(module_name)
        try:
            return getattr(module, class_name)
        except AttributeError as e:
            raise ImproperlyConfigured(
                f"drfautoapi: a classe configurada '{dotted_path}' não existe."
            ) from e

    @staticmethod
    def check_declared_model(found_class, model):
        """Uma classe achada pelo nome não serve a um model diferente do que
        ela declara: é o caso de models de mesmo nome em apps diferentes."""
        declared = getattr(getattr(found_class, "Meta", None), "model", None)
        if declared is not None and declared is not model:
            raise ImproperlyConfigured(
                f"drfautoapi: {found_class.__module__}.{found_class.__name__} declara "
                f"o model {declared._meta.label} e foi achada pelo nome para "
                f"{model._meta.label}."
            )

    @classmethod
    def build_class(
        cls,
        apps_or_models,
        SERIALIZER_MODULE=None,
        FILTER_MODULE=None,
        SERIALIZER_MIXIN=None,
        FILTERSET_MIXIN=None,
    ):

        DRFAUTOAPI = settings.DRFAUTOAPI

        serializers_classes = {}
        filters_classes = {}

        global_serializer_mixin = rest_serializers.ModelSerializer
        global_filter_class = ApiFilterSetMixin

        SERIALIZER_MODULE = SERIALIZER_MODULE or (
            DRFAUTOAPI and DRFAUTOAPI.get("DEFAULT_SERIALIZER_MODULE", None)
        )
        FILTER_MODULE = FILTER_MODULE or (
            DRFAUTOAPI and DRFAUTOAPI.get("DEFAULT_FILTER_MODULE", None)
        )

        SERIALIZER_MIXIN = SERIALIZER_MIXIN or (
            DRFAUTOAPI and DRFAUTOAPI.get("GLOBAL_SERIALIZER_MIXIN", None)
        )
        FILTERSET_MIXIN = FILTERSET_MIXIN or (
            DRFAUTOAPI and DRFAUTOAPI.get("GLOBAL_FILTERSET_MIXIN", None)
        )

        # um módulo ou mixin configurado que não importa interrompe a geração:
        # seguir sem ele deixaria as rotas sem as classes próprias
        if SERIALIZER_MODULE:
            modules = (
                SERIALIZER_MODULE.split(",")
                if isinstance(SERIALIZER_MODULE, str)
                else SERIALIZER_MODULE
            )
            for ms in modules:
                module = cls.import_configured_module(ms)
                imported_classes = inspect.getmembers(module)
                serializers_classes.update(
                    {
                        i[0]: i[1]
                        for i in filter(
                            lambda x: x[0].endswith("Serializer"),
                            imported_classes,
                        )
                    }
                )

        if FILTER_MODULE:
            modules = (
                FILTER_MODULE.split(",")
                if isinstance(FILTER_MODULE, str)
                else FILTER_MODULE
            )
            for mf in modules:
                module = cls.import_configured_module(mf)
                imported_classes = inspect.getmembers(module)
                filters_classes.update(
                    {
                        i[0]: i[1]
                        for i in filter(
                            lambda x: x[0].endswith("FilterSet"),
                            imported_classes,
                        )
                    }
                )

        if FILTERSET_MIXIN:
            global_filter_class = cls.import_configured_class(FILTERSET_MIXIN)

        if SERIALIZER_MIXIN:
            global_serializer_mixin = cls.import_configured_class(SERIALIZER_MIXIN)

        built_sets = {}

        def build(_model):
            object_name = _model._meta.object_name

            serializer_name = f"{object_name}Serializer"
            _serializer_class = serializers_classes.get(
                serializer_name, global_serializer_mixin
            )

            filter_name = f"{object_name}FilterSet"
            _filterset_class = filters_classes.get(filter_name, global_filter_class)

            for found_class in (
                serializers_classes.get(serializer_name),
                filters_classes.get(filter_name),
            ):
                if found_class is not None:
                    cls.check_declared_model(found_class, _model)

            def create_class():

                _meta_serializer = (
                    object
                    if not hasattr(_serializer_class, "Meta")
                    else _serializer_class.Meta
                )

                class ApiSerializer(_serializer_class):

                    class Meta(_meta_serializer):
                        if not hasattr(_meta_serializer, "ref_name"):
                            ref_name = f"{object_name}Serializer"

                        if not hasattr(_meta_serializer, "model"):
                            model = _model

                        if hasattr(_meta_serializer, "exclude"):
                            exclude = _meta_serializer.exclude
                        else:
                            if not hasattr(_meta_serializer, "fields"):
                                fields = "__all__"
                            elif _meta_serializer.fields != "__all__":
                                fields = list(_meta_serializer.fields)
                            else:
                                fields = _meta_serializer.fields

                _meta_filterset = (
                    object
                    if not hasattr(_filterset_class, "Meta")
                    else _filterset_class.Meta
                )

                class ApiFilterSet(_filterset_class):

                    class Meta(
                        _meta_filterset,
                    ):
                        if not hasattr(_meta_filterset, "model"):
                            model = _model

                ApiSerializer.__name__ = serializer_name
                ApiFilterSet.__name__ = filter_name

                @cls.LastModifiedDecorator()
                class ModelApiViewSet(ApiViewSetConstrutor.ApiViewSet):
                    queryset = _model.objects.all()
                    filterset_class = ApiFilterSet
                    serializer_class = ApiSerializer

                return ModelApiViewSet

            viewset = create_class()
            viewset.__name__ = "%sModelViewSet" % _model.__name__
            return viewset

        for am in apps_or_models:

            if isinstance(am, ModelBase):
                app = am._meta.app_config
            else:
                app = am

            if app not in cls._built_sets:
                cls._built_sets[app] = {}

            if am != app:
                cls._built_sets[app][am] = build(am)
                continue

            for model in app.get_models():
                cls._built_sets[app][model] = build(model)

        return cls


# Toda Classe construida acima, pode ser redefinida e aplicado quaisquer
# das possibilidades para uma classe normal criada a partir de
# rest_framework.viewsets.ModelViewSet conforme exemplo para a classe autor

# decorator que processa um endpoint detail trivial com base no model passado,
# Um endpoint detail geralmente é um conteúdo baseado numa FK com outros possíveis filtros
# e os passados pelo proprio cliente, além de o serializer e o filterset
# ser desse model passado


class wrapper_queryset_response_for_drf_action(object):

    def __init__(self, model):
        self.model = model

    def __call__(self, cls):

        def wrapper(instance_view, *args, **kwargs):
            # recupera a viewset do model anotado
            iv = instance_view
            viewset_from_model = ApiViewSetConstrutor._built_sets[
                self.model._meta.app_config
            ][self.model]

            # apossa da instancia da viewset mae do action
            # em uma viewset que processa dados do model passado no decorator
            iv.queryset = viewset_from_model.queryset
            iv.serializer_class = viewset_from_model.serializer_class
            iv.filterset_class = viewset_from_model.filterset_class

            iv.queryset = instance_view.filter_queryset(iv.get_queryset())

            # chama efetivamente o metodo anotado que deve devolver um queryset
            # com os filtros específicos definido pelo programador customizador
            qs = cls(instance_view, *args, **kwargs)

            page = iv.paginate_queryset(qs)
            data = iv.get_serializer(page if page is not None else qs, many=True).data

            return (
                iv.get_paginated_response(data) if page is not None else Response(data)
            )

        return wrapper


# decorator para recuperar e transformar o default
class customize(object):

    def __init__(self, model):
        self.model = model

    def __call__(self, cls):

        class _ApiViewSet(
            cls,
            ApiViewSetConstrutor._built_sets[self.model._meta.app_config][self.model],
        ):
            constructor = ApiViewSetConstrutor

        if hasattr(_ApiViewSet, "build"):
            _ApiViewSet = _ApiViewSet.build()

        ApiViewSetConstrutor._built_sets[self.model._meta.app_config][
            self.model
        ] = _ApiViewSet
        return _ApiViewSet


class DrfAutoApiSerializerMixin(rest_serializers.ModelSerializer):
    """
    Mixin de Serializer que implementa expansão dinâmica de campos
    via parâmetros de query string:
    - `expand`: expande os campos informados
    - `include`: inclui apenas os campos informados
    - `exclude`: exclui os campos informados

    Exemplo:
    - ?expand=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
    - ?include=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
    - ?exclude=campo1;campo2.sub_campo1,sub_campo2;campo3.sub_campo1.sub_sub_campo1,sub_sub_campo2
    - ?expand=campo1&include=campo1.id,name&exclude=campo1.secret_field

    Onde:
    - campo1, campo2, campo3 são campos do model raiz
    - sub_campo1, sub_campo2 são campos relacionados do campo2
    - sub_sub_campo1, sub_sub_campo2 são campos relacionados do sub_campo1

    Ou seja:
    ";" separa campos independentes do nível atual
    "," separa campos relacionados do mesmo campo pai
    "." indica o nível de profundidade dos campos relacionados

    e ainda:
    - `expand` pode ser usado para expansão direta, ou seja, campo1.sub_campo1 já expande campo1
    - `expand`, `include` e `exclude` podem ser usados juntos na mesma requisição
    - `include` e `exclude` só funcionam em subniveis se o campo pai estiver expandido
    - `include` tem precedência sobre `exclude` e já remove todo o resto
    - `exclude` remove o campo do resultado final, mesmo que esteja em `include`
    - Se nenhum dos parâmetros for informado, nenhum campo será expandido
    - Filtros da API, paginação (`page` e `page_size`) e ordenação (`o`)
        podem ser usados normalmente para filtrar os resultados

    Atenção:
    - A expansão não é aplicada para o model User do Django
    - A expansão não é aplicada para campos customizados que utilizam SerializerMethodField
    - Uma exceção é lançada e registrada no log caso ocorra algum erro na expansão de algum campo,
        inclusive devido a recursão infinita
    - A expansão automática de todos os campos relacionados (expand=all) está desabilitada
        por necessidade de controle mais refinado.
    - A expansão de campos relacionados ForeignKey e OneToOne é suportada.
    - A expansão de campos relacionados ManyToMany é suportada.
    - A expansão de campos relacionados reversos (related_name) não é suportada, mas pode ser implementada manualmente no serializer customizado, ou vir a ser implementada no futuro.
    - A expansão de campos relacionados genéricos (GenericForeignKey) não é suportada.
    - **selection_related e prefetch_related** não são aplicados automaticamente, podendo ser implementados manualmente na viewset customizada, ou vir a ser implementados no futuro.
    """

    __str__ = rest_serializers.SerializerMethodField()
    __label__ = rest_serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        max_expand_depth = 5
        max_expand_paths = 8

    def get___str__(self, obj) -> str:
        return str(obj)

    def get___label__(self, obj) -> str:
        return obj._meta.db_table

    @cached_property
    def user_model(self):
        return get_user_model()

    def get_control_fields(self, control_field="expand"):
        request = self.context.get("request", None)
        if request and not self.context.get("drf_ignore_control_params"):
            param = request.query_params.get(control_field, "")
            param = [e.strip() for e in param.split(";") if e.strip()]
            param = [e.split(".") for e in param]
            return param
        return []

    def check_expand_paths(self, expand_fields):
        """Uma requisição não pede mais caminhos de ``expand`` do que o teto.
        Cada alternativa separada por vírgula num nível conta um caminho."""
        limit = getattr(self.Meta, "max_expand_paths", 8)
        total = 0
        for path in expand_fields:
            alternatives = 1
            for level in path:
                alternatives *= len([name for name in level.split(",") if name.strip()])
            total += alternatives
        if limit and total > limit:
            raise rest_serializers.ValidationError(
                {
                    "expand": [
                        f"O expand aceita até {limit} caminhos por requisição; "
                        f"esta pede {total}."
                    ]
                }
            )

    def get_fields(self):
        fields = super().get_fields()

        if not hasattr(self.root, "drf_expand_fields"):
            self.root.drf_expand_fields = self.get_control_fields("expand")
            self.check_expand_paths(self.root.drf_expand_fields)
            self.root.drf_include_fields = self.get_control_fields("include")
            self.root.drf_exclude_fields = self.get_control_fields("exclude")
            if not (
                self.root.drf_expand_fields
                or self.root.drf_include_fields
                or self.root.drf_exclude_fields
            ):
                return fields

        model = self.Meta.model
        expand_fields = self.root.drf_expand_fields
        include_fields = self.root.drf_include_fields
        exclude_fields = self.root.drf_exclude_fields

        expand_all = ["all"] in expand_fields

        if expand_all:
            request = self.context.get("request", None)
            user = getattr(request, "user", None)
            expand_all = user and user.is_superuser

        def parents(nd):
            if not nd:
                return []
            return parents(nd.parent) + [nd.field_name]

        sources = parents(self)
        sources = list(filter(lambda x: x, sources))

        if expand_fields:
            exps = []
            for exp in expand_fields:
                max_expanded_depth = getattr(self.Meta, "max_expand_depth", 5)
                if max_expanded_depth and len(exp) > max_expanded_depth:
                    exp = exp[0 : max(0, max_expanded_depth)]
                if len(exp) > len(sources) and exp[0 : len(sources)] == sources:
                    exps.extend(exp[len(sources)].split(","))
            expand_fields = exps

        if include_fields:
            incls = []
            for inf in include_fields:
                if len(inf) - 1 == len(sources) and inf[:-1] == sources:
                    incls.extend(inf[-1].split(","))
            if incls:
                fields = OrderedDict([(k, v) for k, v in fields.items() if k in incls])

        if exclude_fields:
            excls = []
            for inf in exclude_fields:
                if len(inf) - 1 == len(sources) and inf[:-1] == sources:
                    excls.extend(inf[-1].split(","))
            if excls:
                fields = OrderedDict(
                    [(k, v) for k, v in fields.items() if k not in excls]
                )

        fields_with_relations_map_model = {
            f.name: f.related_model
            for f in model._meta.get_fields()
            if f.is_relation and f.name in fields
        }

        set_fields_with_relations = set(fields_with_relations_map_model.keys())
        set_expand_fields = set(expand_fields)
        set_fields_serialized = set(
            map(
                lambda kv: kv[0],
                filter(
                    lambda kv: not isinstance(
                        kv[1], rest_serializers.SerializerMethodField
                    ),
                    fields.items(),
                ),
            )
        )

        expand_fields = set_fields_with_relations.intersection(set_fields_serialized)

        if not expand_all:
            expand_fields = expand_fields.intersection(set_expand_fields)

        # remove o User model da expansão
        if self.user_model in fields_with_relations_map_model.values():
            expand_fields = [
                f
                for f in expand_fields
                if fields_with_relations_map_model[f] != self.user_model
            ]

        if not expand_fields:
            return fields

        for field_name in expand_fields:
            field = fields[field_name]

            model = fields_with_relations_map_model[field_name]

            if model:
                try:
                    # só expande o que o usuário poderia ler na rota do model
                    # relacionado; sem isso, o campo segue como id
                    view = self.get_expand_view(model)
                    if view is None:
                        continue

                    serializer_class = expand_serializer_class(
                        view.get_serializer_class()
                    )
                    if (
                        hasattr(field, "many")
                        and field.many
                        or isinstance(field, ManyRelatedField)
                    ):
                        serializer_class = serializer_class(
                            many=True, read_only=True, context=self.context
                        )
                        serializer_class.child.drf_expand_view = view
                    else:
                        serializer_class = serializer_class(
                            read_only=True, context=self.context
                        )
                        serializer_class.drf_expand_view = view

                    fields[field_name] = serializer_class

                except Exception as e:
                    logger.error(
                        f"Erro ao expandir campo {field_name} do model {model}: {e}"
                    )

        return fields

    def get_expand_view(self, model):
        """Viewset do model relacionado, pronto para leitura pelo usuário da
        requisição, ou None se ele não puder ler a rota desse model."""
        if not hasattr(self.root, "drf_expand_views"):
            self.root.drf_expand_views = {}
        views = self.root.drf_expand_views

        if model not in views:
            views[model] = None
            request = self.context.get("request", None)
            if request is not None:
                try:
                    views[model] = build_expand_view(model, request)
                except Exception as e:
                    logger.error(
                        f"Erro ao conferir a leitura do model {model} na expansão: {e}"
                    )
        return views[model]


class ExpandReadRequest:
    """A requisição em curso, vista como leitura. Serve para conferir se o
    usuário leria a rota de um model relacionado, qualquer que seja o método
    da requisição original."""

    method = "GET"

    def __init__(self, request):
        self._request = request

    def __getattr__(self, name):
        return getattr(self._request, name)


def build_expand_view(model, request):
    """Instancia o viewset do model como numa listagem e aplica as permissões
    dele. Devolve None se alguma negar a leitura."""
    view = ApiViewSetConstrutor.get_viewset_for_model(model)()
    view.request = ExpandReadRequest(request)
    view.action = "list"
    view.args = ()
    view.kwargs = {}
    view.format_kwarg = None

    for permission in view.get_permissions():
        if not permission.has_permission(view.request, view):
            return None

    # só confere objeto a objeto quando o viewset restringe o queryset
    view.drf_expand_restricts_queryset = ApiViewSetConstrutor.restricts_queryset(model)
    return view


_expand_serializer_classes = {}


def expand_serializer_class(serializer_class):
    """Deriva o serializer usado na expansão: o objeto que o usuário não veria
    na rota do model relacionado sai como id, como se não fosse expandido."""
    if serializer_class not in _expand_serializer_classes:

        class ExpandSerializer(serializer_class):
            drf_expand_view = None

            def to_representation(self, obj):
                if not expand_object_is_visible(self, obj):
                    return obj.pk
                return super().to_representation(obj)

        ExpandSerializer.__name__ = serializer_class.__name__
        _expand_serializer_classes[serializer_class] = ExpandSerializer
    return _expand_serializer_classes[serializer_class]


def expand_object_is_visible(serializer, obj):
    view = serializer.drf_expand_view
    if view is None or not view.drf_expand_restricts_queryset:
        return True

    if not hasattr(serializer.root, "drf_expand_visible"):
        serializer.root.drf_expand_visible = {}
    visible = serializer.root.drf_expand_visible

    key = (type(obj), obj.pk)
    if key not in visible:
        try:
            visible[key] = view.get_queryset().filter(pk=obj.pk).exists()
        except Exception as e:
            logger.error(f"Erro ao conferir a visibilidade de {key} na expansão: {e}")
            visible[key] = False
    return visible[key]


def request_view(request):
    """Viewset que atende a requisição, ou None fora de uma requisição da API."""
    context = getattr(request, "parser_context", None) or {}
    return context.get("view", None)


def readable_field_names(view, request):
    """Nomes dos campos que o serializer do viewset entrega ao usuário da
    requisição, sem contar ``expand``, ``include`` e ``exclude``. Se o
    serializer não puder ser montado, nenhum campo conta como legível."""
    cache = view.__dict__.setdefault("drf_readable_field_names", {})
    try:
        serializer_class = view.get_serializer_class()
        if serializer_class not in cache:
            # o contexto é montado aqui porque o filterset também roda antes
            # de o viewset receber `request` e `format_kwarg`
            context = {
                "request": request,
                "view": view,
                "format": getattr(view, "format_kwarg", None),
                "drf_ignore_control_params": True,
            }
            fields = serializer_class(context=context).fields
            names = set(fields)
            names.update(
                field.source.split(".")[0]
                for field in fields.values()
                if field.source and field.source != "*"
            )
            cache[serializer_class] = names
        return cache[serializer_class]
    except Exception as e:
        logger.error(f"Erro ao levantar os campos legíveis de {view}: {e}")
        return set()


def allowed_ordering(filterset, value):
    """Termos de ``o``, se todos ordenam por campos que o usuário recebe.
    Basta um termo fora disso para a ordenação inteira ser ignorada."""
    terms = [term.strip() for term in value.split(",") if term.strip()]

    view = request_view(filterset.request)
    if view is None:
        # uso do filterset fora de uma requisição da API
        return terms

    model = filterset._meta.model
    for term in terms:
        path = term.lstrip("-")
        if path == "?":
            continue
        hops = path.split("__")
        if not ordering_path_is_readable(view, filterset.request, model, hops):
            return []
    return terms


def ordering_path_is_readable(view, request, model, hops):
    """Cada passo do caminho é um campo legível, e uma relação só é
    atravessada quando o ``expand`` a expandiria para o usuário."""
    hop, rest = hops[0], hops[1:]
    if hop == "pk":
        hop = model._meta.pk.name

    if hop not in readable_field_names(view, request):
        return False
    if not rest:
        return True

    try:
        related = model._meta.get_field(hop).related_model
    except FieldDoesNotExist:
        return False
    if related is None or related is get_user_model():
        return False

    try:
        related_view = build_expand_view(related, request)
    except Exception as e:
        logger.error(f"Erro ao conferir a leitura do model {related} na ordenação: {e}")
        return False
    if related_view is None:
        return False
    return ordering_path_is_readable(related_view, related_view.request, related, rest)
