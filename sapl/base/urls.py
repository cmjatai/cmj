import os

from django.urls.conf import re_path, include
from django.contrib.auth import views
from django.contrib.auth.decorators import permission_required
from django.views.generic.base import RedirectView, TemplateView

from sapl import base
from sapl.base.views import AutorCrud, ConfirmarEmailView, TipoAutorCrud, get_estatistica,\
    OperadorAutorCrud

from sapl.settings import EMAIL_SEND_USER, MEDIA_URL

from .apps import AppConfig
from .views import (AppConfigCrud, CasaLegislativaCrud,
                    CreateUsuarioView, DeleteUsuarioView, EditUsuarioView,
                    HelpTopicView, PesquisarUsuarioView, LogotipoView,
                    RelatorioAtasView, RelatorioAudienciaView,
                    RelatorioDataFimPrazoTramitacaoView,
                    RelatorioHistoricoTramitacaoView,
                    RelatorioMateriasPorAnoAutorTipoView,
                    RelatorioMateriasPorAutorView,
                    RelatorioMateriasTramitacaoView,
                    RelatorioPresencaSessaoView,
                    RelatorioReuniaoView,
                    RelatorioNormasPublicadasMesView,
                    RelatorioNormasVigenciaView,
                    EstatisticasAcessoNormas,
                    RelatoriosListView,
                    ListarInconsistenciasView, ListarProtocolosDuplicadosView,
                    ListarProtocolosComMateriasView, ListarMatProtocoloInexistenteView,
                    ListarParlamentaresDuplicadosView,
                    ListarFiliacoesSemDataFiliacaoView, ListarMandatoSemDataInicioView,
                    ListarParlMandatosIntersecaoView, ListarParlFiliacoesIntersecaoView,
                    ListarAutoresDuplicadosView, ListarBancadaComissaoAutorExternoView,
                    ListarLegislaturaInfindavelView, ListarAnexadasCiclicasView,
                    ListarAnexadosCiclicosView,
                    RelatorioHistoricoTramitacaoAdmView, RelatorioDocumentosAcessoriosView,
                    RelatorioNormasPorAutorView)


app_name = AppConfig.name

admin_user = [
    re_path(r'^sistema/usuario/$', PesquisarUsuarioView.as_view(), name='usuario'),
    re_path(r'^sistema/usuario/create$',
        CreateUsuarioView.as_view(), name='user_create'),
    re_path(r'^sistema/usuario/(?P<pk>\d+)/edit$',
        EditUsuarioView.as_view(), name='user_edit'),
    re_path(r'^sistema/usuario/(?P<pk>\d+)/delete$',
        DeleteUsuarioView.as_view(), name='user_delete')
]


urlpatterns = [
    re_path(r'^sistema/autor/tipo', include(TipoAutorCrud.get_urls())),
    re_path(r'^sistema/autor', include(AutorCrud.get_urls() +
                                   OperadorAutorCrud.get_urls())),

    re_path(r'^sistema/ajuda/(?P<topic>\w+)$',
        HelpTopicView.as_view(), name='help_topic'),
    re_path(r'^sistema/ajuda/$', TemplateView.as_view(template_name='ajuda.html'),
        name='help'),
    re_path(r'^sistema/casa-legislativa', include(CasaLegislativaCrud.get_urls()),
        name="casa_legislativa"),
    re_path(r'^sistema/app-config', include(AppConfigCrud.get_urls())),

    # TODO mover estas telas para a app 'relatorios'
    re_path(r'^sistema/relatorios/$',
        RelatoriosListView.as_view(), name='relatorios_list'),
    re_path(r'^sistema/relatorios/materia-por-autor$',
        RelatorioMateriasPorAutorView.as_view(), name='materia_por_autor'),
    re_path(r'^sistema/relatorios/relatorio-por-mes$',
        RelatorioNormasPublicadasMesView.as_view(), name='normas_por_mes'),
    re_path(r'^sistema/relatorios/relatorio-por-vigencia$',
        RelatorioNormasVigenciaView.as_view(), name='normas_por_vigencia'),
    re_path(r'^sistema/relatorios/estatisticas-acesso$',
        EstatisticasAcessoNormas.as_view(), name='estatisticas_acesso'),
    re_path(r'^sistema/relatorios/materia-por-ano-autor-tipo$',
        RelatorioMateriasPorAnoAutorTipoView.as_view(),
        name='materia_por_ano_autor_tipo'),
    re_path(r'^sistema/relatorios/materia-por-tramitacao$',
        RelatorioMateriasTramitacaoView.as_view(),
        name='materia_por_tramitacao'),
    re_path(r'^sistema/relatorios/historico-tramitacoes$',
        RelatorioHistoricoTramitacaoView.as_view(),
        name='historico_tramitacoes'),
    re_path(r'^sistema/relatorios/data-fim-prazo-tramitacoes$',
        RelatorioDataFimPrazoTramitacaoView.as_view(),
        name='data_fim_prazo_tramitacoes'),
    re_path(r'^sistema/relatorios/presenca$',
        RelatorioPresencaSessaoView.as_view(),
        name='presenca_sessao'),
    re_path(r'^sistema/relatorios/atas$',
        RelatorioAtasView.as_view(),
        name='atas'),
    re_path(r'^sistema/relatorios/reuniao$',
        RelatorioReuniaoView.as_view(),
        name='reuniao'),
    re_path(r'^sistema/relatorios/audiencia$',
        RelatorioAudienciaView.as_view(),
        name='audiencia'),
    re_path(r'^sistema/relatorios/historico-tramitacoesadm$',
        RelatorioHistoricoTramitacaoAdmView.as_view(),
        name='historico_tramitacoes_adm'),
    re_path(r'^sistema/relatorios/documentos_acessorios$',
        RelatorioDocumentosAcessoriosView.as_view(),
        name='relatorio_documentos_acessorios'),
    re_path(r'^sistema/relatorios/normas-por-autor$',
        RelatorioNormasPorAutorView.as_view(), name='normas_por_autor'),

    re_path(r'^email/validate/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        ConfirmarEmailView.as_view(), name='confirmar_email'),

    re_path(r'^sistema/inconsistencias/$',
        ListarInconsistenciasView.as_view(),
        name='lista_inconsistencias'),
    re_path(r'^sistema/inconsistencias/protocolos_duplicados$',
        ListarProtocolosDuplicadosView.as_view(),
        name='lista_protocolos_duplicados'),
    re_path(r'^sistema/inconsistencias/protocolos_com_materias$',
        ListarProtocolosComMateriasView.as_view(),
        name='lista_protocolos_com_materias'),
    re_path(r'^sistema/inconsistencias/materias_protocolo_inexistente$',
        ListarMatProtocoloInexistenteView.as_view(),
        name='lista_materias_protocolo_inexistente'),
    re_path(r'^sistema/inconsistencias/filiacoes_sem_data_filiacao$',
        ListarFiliacoesSemDataFiliacaoView.as_view(),
        name='lista_filiacoes_sem_data_filiacao'),
    re_path(r'^sistema/inconsistencias/mandato_sem_data_inicio',
        ListarMandatoSemDataInicioView.as_view(),
        name='lista_mandato_sem_data_inicio'),
    re_path(r'^sistema/inconsistencias/parlamentares_duplicados$',
        ListarParlamentaresDuplicadosView.as_view(),
        name='lista_parlamentares_duplicados'),
    re_path(r'^sistema/inconsistencias/parlamentares_mandatos_intersecao$',
        ListarParlMandatosIntersecaoView.as_view(),
        name='lista_parlamentares_mandatos_intersecao'),
    re_path(r'^sistema/inconsistencias/parlamentares_filiacoes_intersecao$',
        ListarParlFiliacoesIntersecaoView.as_view(),
        name='lista_parlamentares_filiacoes_intersecao'),
    re_path(r'^sistema/inconsistencias/autores_duplicados$',
        ListarAutoresDuplicadosView.as_view(),
        name='lista_autores_duplicados'),
    re_path(r'^sistema/inconsistencias/bancada_comissao_autor_externo$',
        ListarBancadaComissaoAutorExternoView.as_view(),
        name='lista_bancada_comissao_autor_externo'),
    re_path(r'^sistema/inconsistencias/legislatura_infindavel$',
        ListarLegislaturaInfindavelView.as_view(),
        name='lista_legislatura_infindavel'),
    re_path(r'sistema/inconsistencias/anexadas_ciclicas$',
        ListarAnexadasCiclicasView.as_view(),
        name='lista_anexadas_ciclicas'),
    re_path(r'sistema/inconsistencias/anexados_ciclicos$',
        ListarAnexadosCiclicosView.as_view(),
        name='lista_anexados_ciclicos'),

    re_path(r'^sistema/estatisticas', get_estatistica),

    # todos os sublinks de sistema devem vir acima deste
    re_path(r'^sistema/$', permission_required('base.view_tabelas_auxiliares')
        (TemplateView.as_view(template_name='sistema.html')),
        name='sistema'),

    # Folhas XSLT e extras referenciadas por documentos migrados do sapl 2.5
    re_path(r'^(sapl/)?XSLT/HTML/(?P<path>.*)$', RedirectView.as_view(
        url=os.path.join(MEDIA_URL, 'sapl/public/XSLT/HTML/%(path)s'),
        permanent=False)),
    # url do logotipo usada em documentos migrados do sapl 2.5
    re_path(r'^(sapl/)?sapl_documentos/props_sapl/logo_casa',
        LogotipoView.as_view(), name='logotipo'),


]
