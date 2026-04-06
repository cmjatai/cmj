from django.urls.conf import include, re_path

from sapl.comissoes.views import (
    AdicionaPautaView,
    CargoCrud,
    ComissaoCrud,
    ComposicaoCrud,
    DocumentoAcessorioCrud,
    MateriasTramitacaoListView,
    ParticipacaoCrud,
    PeriodoComposicaoCrud,
    RemovePautaView,
    ReuniaoCrud,
    TipoComissaoCrud,
    get_participacoes_comissao,
)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(
        r"^comissao",
        include(
            ComissaoCrud.get_urls()
            + ComposicaoCrud.get_urls()
            + ReuniaoCrud.get_urls()
            + ParticipacaoCrud.get_urls()
            + DocumentoAcessorioCrud.get_urls()
        ),
    ),
    re_path(
        r"^comissao/(?P<pk>\d+)/materias-em-tramitacao$",
        MateriasTramitacaoListView.as_view(),
        name="materias_em_tramitacao",
    ),
    re_path(
        r"^comissao/(?P<pk>\d+)/pauta/add",
        AdicionaPautaView.as_view(),
        name="pauta_add",
    ),
    re_path(
        r"^comissao/(?P<pk>\d+)/pauta/remove",
        RemovePautaView.as_view(),
        name="pauta_remove",
    ),
    re_path(r"^sistema/comissao/cargo", include(CargoCrud.get_urls())),
    re_path(
        r"^sistema/comissao/periodo-composicao",
        include(PeriodoComposicaoCrud.get_urls()),
    ),
    re_path(r"^sistema/comissao/tipo", include(TipoComissaoCrud.get_urls())),
    re_path(r"^sistema/comissao/recupera-participacoes", get_participacoes_comissao),
]
