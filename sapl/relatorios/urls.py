from django.urls.conf import re_path

from sapl.relatorios.views import RelatorioGestaoView, RelatorioMateriasPorAutorView

from .apps import AppConfig
from .views_old import (relatorio_capa_processo, RelatorioPautaSessao,
                    relatorio_documento_administrativo, relatorio_espelho,
                    relatorio_etiqueta_protocolo, relatorio_materia,
                    relatorio_ordem_dia, relatorio_pauta_sessao,
                    relatorio_protocolo, relatorio_sessao_plenaria,
                    resumo_ata_pdf, relatorio_sessao_plenaria_pdf)


app_name = AppConfig.name


urlpatterns = [


    # Relatórios Refatorados
    re_path(r'^sistema/relatorios/materia-por-autor$',
        RelatorioMateriasPorAutorView.as_view(), name='materia_por_autor'),


    re_path(r'^gestao/(?P<ano>[0-9]+)\.?(?P<format>pdf)?$', RelatorioGestaoView.as_view(),
            name='gestao_render'),








    # Relatórios Antigos

    re_path(r'^relatorios/sessao/(?P<pk>\d+)/pauta$',
        RelatorioPautaSessao.as_view(), name='rel_sessao_pauta'),



    # weaseprint
    re_path(r'^relatorios/(?P<pk>\d+)/sessao-plenaria-pdf$',
        relatorio_sessao_plenaria_pdf, name='relatorio_sessao_plenaria_pdf'),
    re_path(r'^relatorios/relatorio-documento-administrativo$',
        relatorio_documento_administrativo,
        name='relatorio_documento_administrativo'),
    re_path(r'^relatorios/(?P<pk>\d+)/resumo_ata$',
        resumo_ata_pdf, name='resumo_ata_pdf'),

    re_path(r'^relatorios/pauta-sessao/(?P<pk>\d+)/$',
        relatorio_pauta_sessao, name='relatorio_pauta_sessao'),

    # url(r'^relatorios/pauta-sessao/(?P<pk>\d+)/$',
    #    relatorio_pauta_sessao, name='relatorio_pauta_sessao'),

    # trml2pdf
    re_path(r'^relatorios/materia$', relatorio_materia, name='relatorio_materia'),
    re_path(r'^relatorios/capa-processo$',
        relatorio_capa_processo, name='relatorio_capa_processo'),
    re_path(r'^relatorios/ordem-dia$', relatorio_ordem_dia,
        name='relatorio_ordem_dia'),
    re_path(r'^relatorios/espelho$', relatorio_espelho,
        name='relatorio_espelho'),
    re_path(r'^relatorios/(?P<pk>\d+)/sessao-plenaria$',
        relatorio_sessao_plenaria, name='relatorio_sessao_plenaria'),
    re_path(r'^relatorios/protocolo$',
        relatorio_protocolo, name='relatorio_protocolo'),
    re_path(r'^relatorios/(?P<nro>\d+)/(?P<ano>\d+)/etiqueta-protocolo$',
        relatorio_etiqueta_protocolo, name='relatorio_etiqueta_protocolo'),

]
