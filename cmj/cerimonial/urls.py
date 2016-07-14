from django.conf.urls import url, include

from cmj.cerimonial.reports import ImpressoEnderecamentoContatoView
from cmj.cerimonial.views import ContatoCrud, TelefoneCrud, EmailCrud,\
    DependenteCrud, LocalTrabalhoCrud, EnderecoCrud, FiliacaoPartidariaCrud,\
    EnderecoPerfilCrud, LocalTrabalhoPerfilCrud, EmailPerfilCrud,\
    TelefonePerfilCrud, DependentePerfilCrud, PerfilCrud, \
    TipoTelefoneCrud,\
    TipoEnderecoCrud, TipoEmailCrud, ParentescoCrud, EstadoCivilCrud,\
    TipoAutoridadeCrud, TipoLocalTrabalhoCrud, OperadoraTelefoniaCrud,\
    NivelInstrucaoCrud, PronomeTratamentoCrud, \
    ContatoFragmentFormPronomesView, StatusProcessoCrud, TopicoProcessoCrud,\
    ClassificacaoProcessoCrud, ProcessoMasterCrud, AssuntoProcessoCrud,\
    ContatoFragmentFormSearchView, ProcessoContatoCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    url(r'^contato/', include(
        ContatoCrud.get_urls() + TelefoneCrud.get_urls() +
        EmailCrud.get_urls() + DependenteCrud.get_urls() +
        LocalTrabalhoCrud.get_urls() + EnderecoCrud.get_urls() +
        FiliacaoPartidariaCrud.get_urls() + ProcessoContatoCrud.get_urls()
    )),

    url(r'^contato/ajax_search_radio_list',
        ContatoFragmentFormSearchView.as_view(),
        name='ajax_search_contatos'),


    url(r'^perfil/', include(
        EnderecoPerfilCrud.get_urls() +
        LocalTrabalhoPerfilCrud.get_urls() +
        EmailPerfilCrud.get_urls() +
        TelefonePerfilCrud.get_urls() +
        DependentePerfilCrud.get_urls() +
        PerfilCrud.get_urls()
    )),

    url(r'^processo/', include(
        ProcessoMasterCrud.get_urls()
    )),

    url(r'^assuntoprocesso/', include(
        AssuntoProcessoCrud.get_urls()
    )),

    url(r'^reports/cerimonial/enderecamentos',
        ImpressoEnderecamentoContatoView.as_view(),
        name='print_impressoenderecamento'),

    url(r'^sistema/cerimonial/tipoautoridade/(?P<pk>\d+)/pronomes_form',
        ContatoFragmentFormPronomesView.as_view(), name='list_pronomes'),

    url(r'^sistema/cerimonial/statusprocesso/',
        include(StatusProcessoCrud.get_urls())),
    url(r'^sistema/cerimonial/classificacaoprocesso/',
        include(ClassificacaoProcessoCrud.get_urls())),
    url(r'^sistema/cerimonial/topicoprocesso/',
        include(TopicoProcessoCrud.get_urls())),
    url(r'^sistema/cerimonial/tipotelefone/',
        include(TipoTelefoneCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoendereco/',
        include(TipoEnderecoCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoemail/',
        include(TipoEmailCrud.get_urls())),
    url(r'^sistema/cerimonial/parentesco/',
        include(ParentescoCrud.get_urls())),
    url(r'^sistema/cerimonial/estadocivil/',
        include(EstadoCivilCrud.get_urls())),
    url(r'^sistema/cerimonial/tipoautoridade/',
        include(TipoAutoridadeCrud.get_urls())),
    url(r'^sistema/cerimonial/tipolocaltrabalho/',
        include(TipoLocalTrabalhoCrud.get_urls())),
    url(r'^sistema/cerimonial/operadoratelefonia/',
        include(OperadoraTelefoniaCrud.get_urls())),
    url(r'^sistema/cerimonial/nivelinstrucao/',
        include(NivelInstrucaoCrud.get_urls())),
    url(r'^sistema/cerimonial/pronometratamento/',
        include(PronomeTratamentoCrud.get_urls())),
]
