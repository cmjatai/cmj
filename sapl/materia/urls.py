from django.urls.conf import re_path, include

from sapl.materia.views import (AcompanhamentoConfirmarView,
                                AcompanhamentoExcluirView,
                                AcompanhamentoMateriaView, AnaliseSimilaridadeCrud, AnexadaCrud,
                                AssuntoMateriaCrud, AutoriaCrud,
                                AutoriaMultiCreateView, ConfirmarProposicao,
                                CriarProtocoloMateriaView, DespachoInicialCrud,
                                DocumentoAcessorioCrud,
                                DocumentoAcessorioEmLoteView,
                                MateriaAnexadaEmLoteView,
                                EtiquetaPesquisaView, FichaPesquisaView,
                                FichaSelecionaView, ImpressosView,
                                LegislacaoCitadaCrud, MateriaAssuntoCrud,
                                MateriaLegislativaCrud,
                                MateriaLegislativaPesquisaView, MateriaTaView,
                                NumeracaoCrud, OrgaoCrud, OrigemCrud,
                                PrimeiraTramitacaoEmLoteView, ProposicaoCrud,
                                ProposicaoDevolvida, ProposicaoPendente,
                                ProposicaoRecebida, ProposicaoTaView,
                                ReceberProposicao, ReciboProposicaoView,
                                RegimeTramitacaoCrud, RelatoriaCrud,
                                StatusTramitacaoCrud, TipoDocumentoCrud,
                                TipoFimRelatoriaCrud, TipoMateriaCrud,
                                TipoProposicaoCrud, TramitacaoCrud,
                                TramitacaoEmLoteView, UnidadeTramitacaoCrud,
                                recuperar_materia,
                                ExcluirTramitacaoEmLoteView, RetornarProposicao,
                                MateriaPesquisaSimplesView,
                                DespachoInicialMultiCreateView,
                                MateriaLegislativaCheckView,
                                CriarDocumentoAcessorioProtocolo)
from sapl.norma.views import NormaPesquisaSimplesView
from sapl.protocoloadm.views import (
    FichaPesquisaAdmView, FichaSelecionaAdmView)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_impressos = [
    re_path(r'^materia/impressos/$',
        ImpressosView.as_view(),
        name='impressos'),
    re_path(r'^materia/impressos/etiqueta-pesquisa/$',
        EtiquetaPesquisaView.as_view(),
        name='impressos_etiqueta'),
    re_path(r'^materia/impressos/ficha-pesquisa/$',
        FichaPesquisaView.as_view(),
        name='impressos_ficha_pesquisa'),
    re_path(r'^materia/impressos/ficha-seleciona/$',
        FichaSelecionaView.as_view(),
        name='impressos_ficha_seleciona'),
    re_path(r'^materia/impressos/norma-pesquisa/$',
        NormaPesquisaSimplesView.as_view(),
        name='impressos_norma_pesquisa'),
    re_path(r'^materia/impressos/materia-pesquisa/$',
        MateriaPesquisaSimplesView.as_view(),
        name='impressos_materia_pesquisa'),
    re_path(r'^materia/impressos/ficha-pesquisa-adm/$',
        FichaPesquisaAdmView.as_view(),
        name='impressos_ficha_pesquisa_adm'),
    re_path(r'^materia/impressos/ficha-seleciona-adm/$',
        FichaSelecionaAdmView.as_view(),
        name='impressos_ficha_seleciona_adm'),
]

urlpatterns_materia = [

    # Esta customização substitui a url do crud desque que ela permaneça antes
    # da inclusão das urls de DespachoInicialCrud
    re_path(r'^materia/(?P<pk>\d+)/despachoinicial/create',
        DespachoInicialMultiCreateView.as_view(),
        name='despacho-inicial-multi'),

    re_path(r'^materia', include(MateriaLegislativaCrud.get_urls() +
                             AnexadaCrud.get_urls() +
                             AutoriaCrud.get_urls() +
                             DespachoInicialCrud.get_urls() +
                             MateriaAssuntoCrud.get_urls() +
                             NumeracaoCrud.get_urls() +
                             LegislacaoCitadaCrud.get_urls() +
                             TramitacaoCrud.get_urls() +
                             RelatoriaCrud.get_urls() +
                             DocumentoAcessorioCrud.get_urls() +
                             AnaliseSimilaridadeCrud.get_urls()
                             )),

    re_path(r'^materia/(?P<pk>[0-9]+)/create_simplificado$',
        CriarProtocoloMateriaView.as_view(),
        name='materia_create_simplificado'),

    re_path(r'^materia/(?P<pk>[0-9]+)/create_doc_acess$',
        CriarDocumentoAcessorioProtocolo.as_view(),
        name='materia_create_doc_acess$'),

    re_path(r'^materia/recuperar-materia',
        recuperar_materia, name='recuperar_materia'),
    re_path(r'^materia/(?P<pk>[0-9]+)/ta$',
        MateriaTaView.as_view(), name='materia_ta'),

    re_path(r'^materia/check$',
        MateriaLegislativaCheckView.as_view(), name='materia_check'),


    re_path(r'^materia/pesquisar-materia$',
        MateriaLegislativaPesquisaView.as_view(), name='pesquisar_materia'),
    re_path(r'^materia/(?P<pk>\d+)/acompanhar-materia/$',
        AcompanhamentoMateriaView.as_view(), name='acompanhar_materia'),
    re_path(r'^materia/(?P<pk>\d+)/acompanhar-confirmar$',
        AcompanhamentoConfirmarView.as_view(),
        name='acompanhar_confirmar'),
    re_path(r'^materia/(?P<pk>\d+)/acompanhar-excluir$',
        AcompanhamentoExcluirView.as_view(),
        name='acompanhar_excluir'),

    re_path(r'^materia/(?P<pk>\d+)/autoria/multicreate',
        AutoriaMultiCreateView.as_view(),
        name='autoria_multicreate'),


    re_path(r'^materia/acessorio-em-lote', DocumentoAcessorioEmLoteView.as_view(),
        name='acessorio_em_lote'),
    re_path(r'^materia/(?P<pk>\d+)/anexada-em-lote', MateriaAnexadaEmLoteView.as_view(),
        name='anexada_em_lote'),
    re_path(r'^materia/primeira-tramitacao-em-lote',
        PrimeiraTramitacaoEmLoteView.as_view(),
        name='primeira_tramitacao_em_lote'),
    re_path(r'^materia/tramitacao-em-lote', TramitacaoEmLoteView.as_view(),
        name='tramitacao_em_lote'),
    re_path(r'^materia/excluir-tramitacao-em-lote', ExcluirTramitacaoEmLoteView.as_view(),
        name='excluir_tramitacao_em_lote'),
]


urlpatterns_proposicao = [
    re_path(r'^proposicao', include(ProposicaoCrud.get_urls())),
    re_path(r'^proposicao/recibo/(?P<pk>\d+)', ReciboProposicaoView.as_view(),
        name='recibo-proposicao'),
    re_path(r'^proposicao/receber/', ReceberProposicao.as_view(),
        name='receber-proposicao'),
    re_path(r'^proposicao/pendente/', ProposicaoPendente.as_view(),
        name='proposicao-pendente'),
    re_path(r'^proposicao/recebida/', ProposicaoRecebida.as_view(),
        name='proposicao-recebida'),
    re_path(r'^proposicao/devolvida/', ProposicaoDevolvida.as_view(),
        name='proposicao-devolvida'),
    re_path(r'^proposicao/confirmar/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)', ConfirmarProposicao.as_view(),
        name='proposicao-confirmar'),
    re_path(r'^sistema/proposicao/tipo',
        include(TipoProposicaoCrud.get_urls())),

    re_path(r'^proposicao/(?P<pk>[0-9]+)/ta$',
        ProposicaoTaView.as_view(), name='proposicao_ta'),

    # deprecated
    # url(r'^proposicao/texto/(?P<pk>\d+)$', proposicao_texto,
    #    name='proposicao_texto'),


    re_path(r'^proposicao/(?P<pk>\d+)/retornar', RetornarProposicao.as_view(),
        name='retornar-proposicao'),

]

urlpatterns_sistema = [
    re_path(r'^sistema/assunto-materia',
        include(AssuntoMateriaCrud.get_urls())),
    re_path(r'^sistema/proposicao/tipo',
        include(TipoProposicaoCrud.get_urls())),
    re_path(r'^sistema/materia/tipo', include(TipoMateriaCrud.get_urls())),
    re_path(r'^sistema/materia/regime-tramitacao',
        include(RegimeTramitacaoCrud.get_urls())),
    re_path(r'^sistema/materia/tipo-documento',
        include(TipoDocumentoCrud.get_urls())),
    re_path(r'^sistema/materia/tipo-fim-relatoria',
        include(TipoFimRelatoriaCrud.get_urls())),
    re_path(r'^sistema/materia/unidade-tramitacao',
        include(UnidadeTramitacaoCrud.get_urls())),
    re_path(r'^sistema/materia/origem', include(OrigemCrud.get_urls())),
    re_path(r'^sistema/materia/status-tramitacao',
        include(StatusTramitacaoCrud.get_urls())),
    re_path(r'^sistema/materia/orgao', include(OrgaoCrud.get_urls())),
]

urlpatterns = urlpatterns_impressos + urlpatterns_materia + \
    urlpatterns_proposicao + urlpatterns_sistema
