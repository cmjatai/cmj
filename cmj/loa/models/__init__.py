from django.utils.translation import gettext_lazy as _

from cmj.loa.models.m_agrupamento import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
)
from cmj.loa.models.m_ajusteloa import (
    OficioAjusteLoa,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
)
from cmj.loa.models.m_emendaloa import (
    EmendaLoa,
    EmendaLoaHistoricoFase,
    EmendaLoaParlamentar,
)
from cmj.loa.models.m_entidade import Entidade, NaturezaJuridica, TipoEntidade
from cmj.loa.models.m_financeiro_execucao import (
    DespesaPaga,
    Empenho,
    EmpenhoEmendaAjuste,
    ReceitaArrecadada,
)
from cmj.loa.models.m_financeiro_orcamento import (
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
from cmj.loa.models.m_loa import Loa, LoaParlamentar
from cmj.loa.models.m_prestacaoconta import (
    ArquivoPrestacaoContaLoa,
    ArquivoPrestacaoContaRegistro,
    PrestacaoContaLoa,
    PrestacaoContaRegistro,
)
from cmj.loa.models.m_registrocontabil import EmendaLoaRegistroContabil
from cmj.loa.models.m_scrap import ScrapRecord

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
