import logging
from calendar import timegm

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.cache import get_conditional_response
from django.utils.http import http_date
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cmj.core.models import AuditLog
from drfautoapi.drfautoapi import ApiViewSetConstrutor

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.filter(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})


class NaoModificado(Exception):
    """A resposta condicional encerra a requisição antes do handler."""

    def __init__(self, response):
        self.response = response


class RespostaCondicionalMixin:
    """Resposta condicional das rotas geradas (docs/specs/api/gerador.md).

    Vale para a lista e o detalhe, em ``GET`` e ``HEAD``, depois da
    autenticação e da permissão. A data vem do registro de auditoria; o
    viewset pode trocar o cálculo definindo ``last_modified_func``.
    """

    OPERACOES_DE_GRAVACAO = ("C", "U", "D")

    def initial(self, request, *args, **kwargs):
        self.ultima_alteracao = None
        super().initial(request, *args, **kwargs)

        self.ultima_alteracao = self.get_ultima_alteracao(request, *args, **kwargs)
        if self.ultima_alteracao is None:
            return

        response = get_conditional_response(
            request._request,
            last_modified=timegm(self.ultima_alteracao.utctimetuple()),
        )
        if response is not None:
            raise NaoModificado(response)

    def handle_exception(self, exc):
        if isinstance(exc, NaoModificado):
            return exc.response
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        ultima_alteracao = getattr(self, "ultima_alteracao", None)
        if ultima_alteracao is not None and response.status_code in (200, 304):
            response["Last-Modified"] = http_date(ultima_alteracao.timestamp())
            # o cliente revalida sempre, e cache intermediário não guarda
            response["Cache-Control"] = "private, no-cache"
        return response

    def get_ultima_alteracao(self, request, *args, **kwargs):
        """Data para a resposta condicional, ou ``None`` quando ela não se
        aplica à requisição."""
        if request.method not in ("GET", "HEAD"):
            return None
        if self.action not in ("list", "retrieve"):
            return None
        # a resposta traz objetos relacionados, que mudam sem o model mudar
        if request.query_params.get("expand"):
            return None
        # o que o usuário vê depende de quem ele é, e não só do model
        if ApiViewSetConstrutor.restricts_queryset(self.queryset.model):
            return None

        try:
            ultima_alteracao = self.last_modified_func(request, *args, **kwargs)
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Erro ao obter last_modified: {e}")
            return None

        # Last-Modified tem precisão de segundo: uma gravação no mesmo segundo
        # da resposta não seria percebida na revalidação
        if ultima_alteracao is None or int(ultima_alteracao.timestamp()) >= int(
            timezone.now().timestamp()
        ):
            return None
        return ultima_alteracao

    def last_modified_func(self, request, *args, **kwargs):
        """Data da última gravação pelo registro de auditoria.

        No detalhe, a do registro, se o usuário o alcança. Na lista, a do
        model inteiro, exclusões inclusive, sem depender dos filtros.
        Pode ser sobrescrito na customização do viewset: há um exemplo em
        sapl/api/views_materia.py.
        """
        model = self.queryset.model
        registros = AuditLog.objects.filter(operation__in=self.OPERACOES_DE_GRAVACAO)

        if self.action == "retrieve":
            pk = self.kwargs[self.lookup_url_kwarg or self.lookup_field]
            if not self.get_queryset().filter(pk=pk).exists():
                return None
            registros = registros.filter(
                content_type=ContentType.objects.get_for_model(model), object_id=pk
            )
        else:
            registros = registros.filter(
                app_name=model._meta.app_label, model_name=model._meta.model_name
            )

        return (
            registros.order_by("-timestamp").values_list("timestamp", flat=True).first()
        )


class LastModifiedDecorator:
    def __call__(self, cls):
        return type(
            cls.__name__,
            (RespostaCondicionalMixin, cls),
            {"__module__": cls.__module__},
        )


SaplApiViewSetConstrutor = ApiViewSetConstrutor
SaplApiViewSetConstrutor.last_modified_class(LastModifiedDecorator)

SaplApiViewSetConstrutor.import_modules(
    [
        "sapl.api.views_audiencia",
        "sapl.api.views_base",
        "sapl.api.views_comissoes",
        "sapl.api.views_compilacao",
        "sapl.api.views_materia",
        "sapl.api.views_norma",
        "sapl.api.views_painel",
        "sapl.api.views_parlamentares",
        "sapl.api.views_protocoloadm",
        "sapl.api.views_sessao",
    ]
)


"""
1. ApiViewSetConstrutor constroi uma rest_framework.viewsets.ModelViewSet
     para todos os models de todas as app_configs passadas no list
2. Define DjangoFilterBackend como ferramenta de filtro dos campos
3. Define Serializer como a seguir:
    3.1   - Define um Serializer genérico para cada módel
    3.1.1 - se existir um DEFAULT_SERIALIZER_MODULE em settings,
            recupera Serializer customizados no módulo DEFAULT_SERIALIZER_MODULE
    3.2 - Para todo model é opcional a existência de {model}Serializer.
          Caso não seja definido um Serializer customizado, utiliza-se o genérico
    3.3 - Caso exista GLOBAL_SERIALIZER_MIXIN definido,
          utiliza este Serializer para construir o genérico de 3.1
4. Define um FilterSet como a seguir:
    4.1 -   Define um FilterSet genérico para cada módel
    4.1.1 - se existir um DEFAULT_FILTER_MODULE em settings,
            recupera o FilterSet customizado no módulo DEFAULT_FILTER_MODULE
    4.2 - Para todo model é opcional a existência de {model}FilterSet.
          Caso não seja definido um FilterSet customizado, utiliza-se o genérico
    4.3 - Caso exista GLOBAL_FILTERSET_MIXIN definido,
          utiliza este FilterSet para construir o genérico de 4.1
    4.4 - Caso não exista GLOBAL_FILTERSET_MIXIN, será aplicado
          drfautoapi.drjautoapi.CmjFilterSetMixin que inclui parametro para:
          - order_by: através do parâmetro "o"
          - amplia os lookups aceitos pelo FilterSet default
            para os aceitos pelo django sem a necessidade de criar
            fields específicos em um FilterSet customizado.

5. ApiViewSetConstrutor não cria padrões e/ou exige conhecimento alem dos
    exigidos pela DRF.

6. As rotas são criadas seguindo nome da app e nome do model
    http://localhost:9000/api/{applabel}/{model_name}/
    e seguem as variações definidas em:
    https://www.django-rest-framework.org/api-guide/routers/#defaultrouter


**ApiViewSetConstrutor._built_sets** é um dict de dicts de models conforme:
    {
        ...

        'audiencia': {
            'tipoaudienciapublica': TipoAudienciaPublicaViewSet,
            'audienciapublica': AudienciaPublicaViewSet,
            'anexoaudienciapublica': AnexoAudienciaPublicaViewSet

            ...

            },

        ...

        'base': {
            'casalegislativa': CasaLegislativaViewSet,
            'appconfig': AppConfigViewSet,

            ...

        }

        ...

    }
"""
