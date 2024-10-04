from django.urls.conf import re_path, include

from sapl.protocoloadm.views import (
    AnularProtocoloAdmView,
    ComprovanteProtocoloView,
    CriarDocumentoProtocolo,
    DocumentoAcessorioAdministrativoCrud,
    DocumentoAdministrativoCrud,
    ProtocoloMateriaTemplateView,
    ProtocoloMateriaView,
    ProtocoloMostrarView,
    ProtocoloPesquisaView,
    StatusTramitacaoAdministrativoCrud,
    recuperar_materia_protocolo,
    TipoDocumentoAdministrativoCrud,
    TramitacaoAdmCrud,
    atualizar_numero_documento,
    DesvincularDocumentoView,
    DesvincularMateriaView,
    AnexadoCrud, DocumentoAnexadoEmLoteView,
    PrimeiraTramitacaoEmLoteAdmView,
    TramitacaoEmLoteAdmView, AcompanhamentoExcluirView,
    AcompanhamentoConfirmarView, AcompanhamentoDocumentoView,
    ProtocoloRedirectConteudoView, ProtocoloDocumentoAcessorioView,
    ProtocoloDocumentoView, ProtocoloHomologarView, VinculoDocAdminMateriaCrud,
    VinculoDocAdminMateriaEmLoteView)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_documento_administrativo = [
    re_path(r'^doc',
        include(DocumentoAdministrativoCrud.get_urls() +
                AnexadoCrud.get_urls() +
                TramitacaoAdmCrud.get_urls() +
                DocumentoAcessorioAdministrativoCrud.get_urls() +
                VinculoDocAdminMateriaCrud.get_urls())),

    re_path(r'^doc/(?P<pk>\d+)/anexado_em_lote', DocumentoAnexadoEmLoteView.as_view(),
        name='anexado_em_lote'),

    re_path(r'^docadm/(?P<pk>\d+)/vinculo-em-lote', VinculoDocAdminMateriaEmLoteView.as_view(),
        name='vinculodocadminmateria_em_lote'),

]

urlpatterns_protocolo = [

    #    url(r'^protocoloadm/protocolo-doc/',
    #        include(ProtocoloDocumentoCrud.get_urls())),
    #    url(r'^protocoloadm/protocolo-mat/',
    #        include(ProtocoloMateriaCrud.get_urls()), name='protocolomat'),
    # url(r'^protocoloadm/protocolo-list$',
    #    ProtocoloListView.as_view(), name='protocolo_list'),

    re_path(r'^protocoloadm/$',
        ProtocoloPesquisaView.as_view(), name='protocolo'),

    re_path(r'^protocoloadm/protocolar-doc$',
        ProtocoloDocumentoView.as_view(), name='protocolar_doc'),


    re_path(r'^protocoloadm/protocolar-doc-acess$',
        ProtocoloDocumentoAcessorioView.as_view(), name='protocolar_doc_acess'),


    re_path(r'^protocoloadm/(?P<pk>\d+)/protocolo-mostrar$',
        ProtocoloMostrarView.as_view(), name='protocolo_mostrar'),



    re_path(r'^protocoloadm/(?P<pk>\d+)/homologar$',
        ProtocoloHomologarView.as_view(), name='protocolo_homologar'),



    re_path(r'^protocoloadm/(?P<pk>\d+)/conteudo$',
        ProtocoloRedirectConteudoView.as_view(), name='redirect_conteudo'),


    re_path(r'^doc/(?P<pk>\d+)/acompanhar-documento/$',
        AcompanhamentoDocumentoView.as_view(), name='acompanhar_documento'),
    re_path(r'^doc/(?P<pk>\d+)/acompanhar-confirmar$',
        AcompanhamentoConfirmarView.as_view(),
        name='acompanhar_confirmar'),
    re_path(r'^doc/(?P<pk>\d+)/acompanhar-excluir$',
        AcompanhamentoExcluirView.as_view(),
        name='acompanhar_excluir'),



    re_path(r'^protocoloadm/(?P<pk>\d+)/continuar$',
        ProtocoloMateriaTemplateView.as_view(), name='materia_continuar'),


    re_path(r'^protocoloadm/anular-protocolo',
        AnularProtocoloAdmView.as_view(), name='anular_protocolo'),
    re_path(r'^protocoloadm/desvincular-documento',
        DesvincularDocumentoView.as_view(), name='desvincular_documento'),
    re_path(r'^protocoloadm/desvincular-materia',
        DesvincularMateriaView.as_view(), name='desvincular_materia'),
    re_path(r'^protocoloadm/protocolar-mat',
        ProtocoloMateriaView.as_view(), name='protocolar_mat'),

    re_path(r'^protocoloadm/(?P<pk>\d+)/comprovante$',
        ComprovanteProtocoloView.as_view(), name='comprovante_protocolo'),
    re_path(r'^protocoloadm/(?P<pk>\d+)/criar-documento$',
        CriarDocumentoProtocolo.as_view(), name='criar_documento'),

    re_path(r'^protocoloadm/atualizar_numero_documento$',
        atualizar_numero_documento, name='atualizar_numero_documento'),
    re_path(r'^protocoloadm/recuperar-materia',
        recuperar_materia_protocolo, name='recuperar_materia_protocolo'),

    re_path(r'^protocoloadm/primeira-tramitacao-em-lote',
        PrimeiraTramitacaoEmLoteAdmView.as_view(),
        name='primeira_tramitacao_em_lote_docadm'),

    re_path(r'^protocoloadm/tramitacao-em-lote', TramitacaoEmLoteAdmView.as_view(),
        name='tramitacao_em_lote_docadm'),
]

urlpatterns_sistema = [
    re_path(r'^sistema/tipo-documento-adm',
        include(TipoDocumentoAdministrativoCrud.get_urls())),
    re_path(r'^sistema/status-tramitacao-adm',
        include(StatusTramitacaoAdministrativoCrud.get_urls())),

    # FIXME: Usado para pesquisar autor- SOLUÇÃO-foi transformado em api/autor
    # Melhor forma de fazer?
    # Deve mudar de app?
    # url(r'^protocoloadm/pesquisar-autor',
    #    pesquisa_autores, name='pesquisar_autor'),
]

urlpatterns = (urlpatterns_documento_administrativo +
               urlpatterns_protocolo +
               urlpatterns_sistema)
