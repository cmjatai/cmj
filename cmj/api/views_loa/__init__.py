import logging

from django.apps.registry import apps

from cmj.api.serializers import PrestacaoContaRegistroSerializer
from cmj.api.views_loa.agrupamento import AgrupamentoViewSet
from cmj.api.views_loa.agrupamentoemendaloa import AgrupamentoEmendaLoaViewSet
from cmj.api.views_loa.agrupamentoregistrocontabil import (
    AgrupamentoRegistroContabilViewSet,
)
from cmj.api.views_loa.arquivoprestacaocontaloa import ArquivoPrestacaoContaLoaViewSet
from cmj.api.views_loa.arquivoprestacaocontaregistro import (
    ArquivoPrestacaoContaRegistroViewSet,
)
from cmj.api.views_loa.despesaconsulta import DespesaConsultaViewSet
from cmj.api.views_loa.emendaloa import EmendaLoaViewSet
from cmj.api.views_loa.emendaloaregistrocontabil import EmendaLoaRegistroContabilViewSet
from cmj.api.views_loa.entidade import EntidadeViewSet
from cmj.api.views_loa.loa import LoaViewSet
from cmj.api.views_loa.oficioajusteloa import OficioAjusteLoaViewSet
from cmj.api.views_loa.registroajusteloa import RegistroAjusteLoaViewSet
from cmj.api.views_loa.subfuncao import SubFuncaoViewSet
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
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class([apps.get_app_config("loa")])


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
