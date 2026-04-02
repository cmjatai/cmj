from django.utils.translation import gettext_lazy as _

from cmj.loa.models.agrupamento import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
)
from cmj.loa.models.ajusteloa import (
    OficioAjusteLoa,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
)
from cmj.loa.models.emendaloa import (
    EmendaLoa,
    EmendaLoaHistoricoFase,
    EmendaLoaParlamentar,
)
from cmj.loa.models.entidade import Entidade, NaturezaJuridica, TipoEntidade
from cmj.loa.models.financeiro_execucao import (
    DespesaPaga,
    Empenho,
    EmpenhoEmendaAjuste,
    ReceitaArrecadada,
)
from cmj.loa.models.financeiro_orcamento import (
    Acao,
    Despesa,
    DespesaConsulta,
    Fonte,
    Funcao,
    Natureza,
    Orgao,
    Programa,
    SubFuncao,
    UnidadeOrcamentaria,
)
from cmj.loa.models.loa import Loa, LoaParlamentar
from cmj.loa.models.prestacaoconta import (
    ArquivoPrestacaoContaLoa,
    ArquivoPrestacaoContaRegistro,
    PrestacaoContaLoa,
    PrestacaoContaRegistro,
)
from cmj.loa.models.registrocontabil import EmendaLoaRegistroContabil
from cmj.loa.models.scrap import ScrapRecord

__all__ = [
    "Agrupamento",
    "AgrupamentoEmendaLoa",
    "AgrupamentoRegistroContabil",
    "OficioAjusteLoa",
    "RegistroAjusteLoa",
    "RegistroAjusteLoaParlamentar",
    "EmendaLoa",
    "EmendaLoaParlamentar",
    "EmendaLoaHistoricoFase",
    "Entidade",
    "TipoEntidade",
    "NaturezaJuridica",
    "DespesaPaga",
    "ReceitaArrecadada",
    "Empenho",
    "EmpenhoEmendaAjuste",
    "Despesa",
    "DespesaConsulta",
    "Orgao",
    "UnidadeOrcamentaria",
    "Funcao",
    "SubFuncao",
    "Programa",
    "Acao",
    "Natureza",
    "Fonte",
    "Loa",
    "LoaParlamentar",
    "PrestacaoContaLoa",
    "ArquivoPrestacaoContaLoa",
    "PrestacaoContaRegistro",
    "ArquivoPrestacaoContaRegistro",
    "EmendaLoaRegistroContabil",
    "ScrapRecord",
]
