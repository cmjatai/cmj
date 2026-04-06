from django.urls.conf import include, re_path

from cmj.cerimonial.reports import (
    ImpressoEnderecamentoContatoView,
    RelatorioContatoAgrupadoPorGrupoView,
    RelatorioContatoAgrupadoPorProcessoView,
)
from cmj.cerimonial.views import (
    AnexoProcessoCrud,
    AssuntoProcessoCrud,
    ClassificacaoProcessoCrud,
    ContatoCrud,
    ContatoFragmentFormPronomesView,
    ContatoFragmentFormSearchView,
    DependenteCrud,
    DependentePerfilCrud,
    EmailCrud,
    EmailPerfilCrud,
    EnderecoCrud,
    EnderecoPerfilCrud,
    EstadoCivilCrud,
    FiliacaoPartidariaCrud,
    GrupoDeContatosMasterCrud,
    LocalTrabalhoCrud,
    LocalTrabalhoPerfilCrud,
    NivelInstrucaoCrud,
    OperadoraTelefoniaCrud,
    ParentescoCrud,
    PerfilCrud,
    ProcessoContatoCrud,
    ProcessoMasterCrud,
    PronomeTratamentoCrud,
    StatusProcessoCrud,
    TelefoneCrud,
    TelefonePerfilCrud,
    TipoAutoridadeCrud,
    TipoEmailCrud,
    TipoEnderecoCrud,
    TipoLocalTrabalhoCrud,
    TipoTelefoneCrud,
    TopicoProcessoCrud,
    VisitaCrud,
)

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    re_path(
        r"^contato",
        include(
            ContatoCrud.get_urls()
            + TelefoneCrud.get_urls()
            + EmailCrud.get_urls()
            + DependenteCrud.get_urls()
            + LocalTrabalhoCrud.get_urls()
            + EnderecoCrud.get_urls()
            + FiliacaoPartidariaCrud.get_urls()
            + ProcessoContatoCrud.get_urls()
        ),
    ),
    re_path(r"^recepcao", include(VisitaCrud.get_urls())),
    re_path(
        r"^contato/ajax_search_radio_list",
        ContatoFragmentFormSearchView.as_view(),
        name="ajax_search_contatos",
    ),
    re_path(
        r"^perfil",
        include(
            EnderecoPerfilCrud.get_urls()
            + LocalTrabalhoPerfilCrud.get_urls()
            + EmailPerfilCrud.get_urls()
            + TelefonePerfilCrud.get_urls()
            + DependentePerfilCrud.get_urls()
            + PerfilCrud.get_urls()
        ),
    ),
    re_path(r"^grupo", include(GrupoDeContatosMasterCrud.get_urls())),
    re_path(
        r"^processo",
        include(ProcessoMasterCrud.get_urls() + AnexoProcessoCrud.get_urls()),
    ),
    re_path(r"^assuntoprocesso", include(AssuntoProcessoCrud.get_urls())),
    re_path(
        r"^reports/cerimonial/enderecamentos",
        ImpressoEnderecamentoContatoView.as_view(),
        name="print_impressoenderecamento",
    ),
    re_path(
        r"^reports/cerimonial/contatos_por_processo",
        RelatorioContatoAgrupadoPorProcessoView.as_view(),
        name="print_rel_contato_agrupado_por_processo",
    ),
    re_path(
        r"^reports/cerimonial/contatos_por_grupo",
        RelatorioContatoAgrupadoPorGrupoView.as_view(),
        name="print_rel_contato_agrupado_por_grupo",
    ),
    re_path(
        r"^sistema/cerimonial/tipoautoridade/(?P<pk>\d+)/pronomes_form",
        ContatoFragmentFormPronomesView.as_view(),
        name="list_pronomes",
    ),
    re_path(
        r"^sistema/cerimonial/statusprocesso", include(StatusProcessoCrud.get_urls())
    ),
    re_path(
        r"^sistema/cerimonial/classificacaoprocesso",
        include(ClassificacaoProcessoCrud.get_urls()),
    ),
    re_path(
        r"^sistema/cerimonial/topicoprocesso", include(TopicoProcessoCrud.get_urls())
    ),
    re_path(r"^sistema/cerimonial/tipotelefone", include(TipoTelefoneCrud.get_urls())),
    re_path(r"^sistema/cerimonial/tipoendereco", include(TipoEnderecoCrud.get_urls())),
    re_path(r"^sistema/cerimonial/tipoemail", include(TipoEmailCrud.get_urls())),
    re_path(r"^sistema/cerimonial/parentesco", include(ParentescoCrud.get_urls())),
    re_path(r"^sistema/cerimonial/estadocivil", include(EstadoCivilCrud.get_urls())),
    re_path(
        r"^sistema/cerimonial/tipoautoridade", include(TipoAutoridadeCrud.get_urls())
    ),
    re_path(
        r"^sistema/cerimonial/tipolocaltrabalho",
        include(TipoLocalTrabalhoCrud.get_urls()),
    ),
    re_path(
        r"^sistema/cerimonial/operadoratelefonia",
        include(OperadoraTelefoniaCrud.get_urls()),
    ),
    re_path(
        r"^sistema/cerimonial/nivelinstrucao", include(NivelInstrucaoCrud.get_urls())
    ),
    re_path(
        r"^sistema/cerimonial/pronometratamento",
        include(PronomeTratamentoCrud.get_urls()),
    ),
]
