import logging

from django.apps.registry import apps

from cmj.api.loa.views.agrupamento import AgrupamentoViewSet
from cmj.api.loa.views.agrupamentoemendaloa import AgrupamentoEmendaLoaViewSet
from cmj.api.loa.views.agrupamentoregistrocontabil import (
    AgrupamentoRegistroContabilViewSet,
)
from cmj.api.loa.views.arquivoprestacaocontaloa import ArquivoPrestacaoContaLoaViewSet
from cmj.api.loa.views.arquivoprestacaocontaregistro import (
    ArquivoPrestacaoContaRegistroViewSet,
)
from cmj.api.loa.views.despesaconsulta import DespesaConsultaViewSet
from cmj.api.loa.views.emendaloa import EmendaLoaViewSet
from cmj.api.loa.views.emendaloaregistrocontabil import EmendaLoaRegistroContabilViewSet
from cmj.api.loa.views.empenho import EmpenhoViewSet
from cmj.api.loa.views.entidade import EntidadeViewSet
from cmj.api.loa.views.loa import LoaViewSet
from cmj.api.loa.views.oficioajusteloa import OficioAjusteLoaViewSet
from cmj.api.loa.views.registroajusteloa import RegistroAjusteLoaViewSet
from cmj.api.loa.views.subfuncao import SubFuncaoViewSet
from cmj.loa.models import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
    ArquivoPrestacaoContaLoa,
    ArquivoPrestacaoContaRegistro,
    DespesaConsulta,
    EmendaLoa,
    EmendaLoaRegistroContabil,
    Entidade,
    Loa,
    OficioAjusteLoa,
    PrestacaoContaRegistro,
    RegistroAjusteLoa,
    SubFuncao,
)
from cmj.loa.models.m_financeiro_execucao import Empenho
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [apps.get_app_config("loa")],
    SERIALIZER_MODULE=[
        "cmj.api.loa.serializers",
    ]
)


@customize(SubFuncao)
class _SubFuncaoViewSet(SubFuncaoViewSet):
    pass


@customize(Loa)
class _LoaViewSet(LoaViewSet):
    pass


@customize(EmendaLoa)
class _EmendaLoaViewSet(EmendaLoaViewSet):
    pass


@customize(DespesaConsulta)
class _DespesaConsultaViewSet(DespesaConsultaViewSet):
    pass


@customize(EmendaLoaRegistroContabil)
class _EmendaLoaRegistroContabilViewSet(EmendaLoaRegistroContabilViewSet):
    pass


@customize(AgrupamentoEmendaLoa)
class _AgrupamentoEmendaLoaViewSet(AgrupamentoEmendaLoaViewSet):
    pass


@customize(Agrupamento)
class _Agrupamento(AgrupamentoViewSet):
    pass


@customize(AgrupamentoRegistroContabil)
class _AgrupamentoRegistroContabilViewSet(AgrupamentoRegistroContabilViewSet):
    pass


@customize(OficioAjusteLoa)
class _OficioAjusteLoaViewSet(OficioAjusteLoaViewSet):
    pass


@customize(RegistroAjusteLoa)
class _RegistroAjusteLoaViewSet(RegistroAjusteLoaViewSet):
    pass


@customize(ArquivoPrestacaoContaLoa)
class _ArquivoPrestacaoContaLoaViewSet(ArquivoPrestacaoContaLoaViewSet):
    pass


@customize(ArquivoPrestacaoContaRegistro)
class _ArquivoPrestacaoContaRegistroViewSet(ArquivoPrestacaoContaRegistroViewSet):
    pass


@customize(PrestacaoContaRegistro)
class _PrestacaoContaRegistroViewSet:
    pass


@customize(Entidade)
class _EntidadeViewSet(EntidadeViewSet):
    pass


@customize(Empenho)
class _EmpenhoViewSet(EmpenhoViewSet):
    pass
