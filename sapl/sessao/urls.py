from django.urls.conf import re_path, include

from sapl.sessao.filterviews import PesquisarSessaoPlenariaView, RegistroVotacaoFilterView
from sapl.sessao.views import (AdicionarVariasMateriasExpediente,
                               AdicionarVariasMateriasOrdemDia,
                               ExpedienteMateriaCrud, ExpedienteView, JustificativaAusenciaCrud,
                               OcorrenciaSessaoView, MateriaOrdemDiaCrud, OradorOrdemDiaCrud,
                               MesaView, OradorCrud,
                               OradorExpedienteCrud, PainelView,
                               PresencaOrdemDiaView, PresencaView,
                               ResumoView, ResumoAtaView, RetiradaPautaCrud, SessaoCrud,
                               TipoJustificativaCrud, TipoExpedienteCrud, TipoResultadoVotacaoCrud,
                               TipoExpedienteCrud, TipoResultadoVotacaoCrud, TipoRetiradaPautaCrud,
                               TipoSessaoCrud, VotacaoEditView,
                               VotacaoExpedienteEditView,
                               VotacaoExpedienteView, VotacaoNominalEditView,
                               VotacaoNominalExpedienteDetailView,
                               VotacaoNominalExpedienteEditView,
                               VotacaoNominalExpedienteView,
                               VotacaoNominalTransparenciaDetailView,
                               VotacaoSimbolicaTransparenciaDetailView,
                               VotacaoNominalView, VotacaoView, abrir_votacao,
                               atualizar_mesa, insere_parlamentar_composicao,
                               mudar_ordem_materia_sessao, recuperar_materia,
                               recuperar_numero_sessao_view,
                               remove_parlamentar_composicao,
                               reordernar_materias_expediente,
                               reordernar_materias_ordem,
                               renumerar_materias_ordem,
                               renumerar_materias_expediente,
                               sessao_legislativa_legislatura_ajax,
                               VotacaoEmBlocoOrdemDia, VotacaoEmBlocoExpediente,
                               VotacaoEmBlocoSimbolicaView, VotacaoEmBlocoNominalView,
                               resumo_ordenacao,
                               recuperar_nome_tipo_sessao,
                               voto_nominal_parlamentar,
                               ExpedienteLeituraView,
                               OrdemDiaLeituraView, retirar_leitura,
                               recuperar_tramitacao)
from sapl.sessao.views_pautas import PautaComissaoDetailView, PautaComissaoView, PautaSessaoDetailView, PautaSessaoView, PesquisarPautaComissaoView, PesquisarPautaSessaoView

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    re_path(r'^sessao', include(SessaoCrud.get_urls() + OradorCrud.get_urls() +
                                OradorExpedienteCrud.get_urls() +
                                ExpedienteMateriaCrud.get_urls() +
                                JustificativaAusenciaCrud.get_urls() +
                                MateriaOrdemDiaCrud.get_urls() +
                                OradorOrdemDiaCrud.get_urls() +
                                RetiradaPautaCrud.get_urls())),

    re_path(r'^sessao/(?P<pk>\d+)/mesa$', MesaView.as_view(), name='mesa'),

    re_path(r'^sessao/mesa/atualizar-mesa/$',
            atualizar_mesa,
            name='atualizar_mesa'),

    re_path(r'^sessao/mesa/insere-parlamentar/composicao/$',
            insere_parlamentar_composicao,
            name='insere_parlamentar_composicao'),

    re_path(r'^sessao/mesa/remove-parlamentar-composicao/$',
            remove_parlamentar_composicao,
            name='remove_parlamentar_composicao'),

    re_path(r'^sessao/recuperar-materia/',
            recuperar_materia, name="recuperar_materia"),
    re_path(r'^sessao/recuperar-tramitacao/', recuperar_tramitacao),

    re_path(r'^sessao/recuperar-numero-sessao/',
            recuperar_numero_sessao_view,
            name='recuperar_numero_sessao_view'
            ),
    re_path(r'^sessao/recuperar-nome-tipo-sessao/',
            recuperar_nome_tipo_sessao,
            name='recuperar_nome_tipo_sessao'),
    re_path(r'^sessao/sessao-legislativa-legislatura-ajax/',
            sessao_legislativa_legislatura_ajax,
            name='sessao_legislativa_legislatura_ajax_view'),

    re_path(r'^sessao/(?P<pk>\d+)/(?P<spk>\d+)/abrir-votacao$',
            abrir_votacao,
            name="abrir_votacao"),
    re_path(r'^sessao/(?P<pk>\d+)/reordenar-expediente$',
            reordernar_materias_expediente,
            name="reordenar_expediente"),
    re_path(r'^sessao/(?P<pk>\d+)/reordenar-ordem$', reordernar_materias_ordem,
            name="reordenar_ordem"),
    re_path(r'^sessao/(?P<pk>\d+)/renumerar-ordem$', renumerar_materias_ordem,
            name="renumerar_ordem"),
    re_path(r'^sessao/(?P<pk>\d+)/renumerar-materias-expediente$', renumerar_materias_expediente,
            name="renumerar_materias_expediente"),
    re_path(r'^sistema/sessao-plenaria/tipo',
            include(TipoSessaoCrud.get_urls())),
    re_path(r'^sistema/sessao-plenaria/tipo-resultado-votacao',
            include(TipoResultadoVotacaoCrud.get_urls())),
    re_path(r'^sistema/sessao-plenaria/tipo-expediente',
            include(TipoExpedienteCrud.get_urls())),
    re_path(r'^sistema/sessao-plenaria/tipo-justificativa',
            include(TipoJustificativaCrud.get_urls())),
    re_path(r'^sistema/sessao-plenaria/tipo-retirada-pauta',
            include(TipoRetiradaPautaCrud.get_urls())),
    re_path(r'^sistema/resumo-ordenacao',
            resumo_ordenacao,
            name='resumo_ordenacao'),
    re_path(r'^sessao/(?P<pk>\d+)/adicionar-varias-materias-expediente/',
            AdicionarVariasMateriasExpediente.as_view(),
            name='adicionar_varias_materias_expediente'),
    re_path(r'^sessao/(?P<pk>\d+)/adicionar-varias-materias-ordem-dia/',
            AdicionarVariasMateriasOrdemDia.as_view(),
            name='adicionar_varias_materias_ordem_dia'),

    # PAUTA SESSÃO
    re_path(r'^sessao/pauta-sessao$',
            PautaSessaoView.as_view(), name='pauta_sessao'),
    re_path(r'^sessao/pauta-sessao/pesquisar-pauta$',
            PesquisarPautaSessaoView.as_view(), name='pesquisar_pauta'),
    re_path(r'^sessao/pauta-sessao/(?P<pk>\d+)$',
            PautaSessaoDetailView.as_view(), name='pauta_sessao_detail'),

    # PAUTA COMISSÃO
    re_path(r'^sessao/pauta-comissao$',
            PautaComissaoView.as_view(), name='pauta_comissao'),
    re_path(r'^sessao/pauta-comissao/pesquisar-pauta$',
            PesquisarPautaComissaoView.as_view(), name='pesquisar_comissao_pauta'),
    re_path(r'^sessao/pauta-comissao/(?P<pk>\d+)$',
            PautaComissaoDetailView.as_view(), name='pauta_comissao_detail'),

    # Subnav sessão
    re_path(r'^sessao/(?P<pk>\d+)/expediente$',
            ExpedienteView.as_view(), name='expediente'),
    re_path(r'^sessao/(?P<pk>\d+)/ocorrencia_sessao$',
            OcorrenciaSessaoView.as_view(), name='ocorrencia_sessao'),
    re_path(r'^sessao/(?P<pk>\d+)/presenca$',
            PresencaView.as_view(), name='presenca'),
    re_path(r'^sessao/(?P<pk>\d+)/painel$',
            PainelView.as_view(), name='painel'),
    re_path(r'^sessao/(?P<pk>\d+)/presencaordemdia$',
            PresencaOrdemDiaView.as_view(),
            name='presencaordemdia'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao_bloco_ordemdia$',
            VotacaoEmBlocoOrdemDia.as_view(),
            name='votacao_bloco_ordemdia'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao_bloco/votnom$',
            VotacaoEmBlocoNominalView.as_view(), name='votacaobloconom'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao_bloco/votsimb$',
            VotacaoEmBlocoSimbolicaView.as_view(), name='votacaoblocosimb'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao_bloco_expediente$',
            VotacaoEmBlocoExpediente.as_view(),
            name='votacao_bloco_expediente'),
    re_path(r'^sessao/(?P<pk>\d+)/resumo$',
            ResumoView.as_view(), name='resumo'),
    re_path(r'^sessao/(?P<pk>\d+)/resumo_ata$',
            ResumoAtaView.as_view(), name='resumo_ata'),
    re_path(r'^sessao/pesquisar-sessao$',
            PesquisarSessaoPlenariaView.as_view(), name='pesquisar_sessao'),


    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votnom/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalView.as_view(), name='votacaonominal'),
    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votnom/edit/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalEditView.as_view(), name='votacaonominaledit'),
    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votsec/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoView.as_view(), name='votacaosecreta'),
    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votsec/view/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoEditView.as_view(), name='votacaosecretaedit'),
    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoView.as_view(), name='votacaosimbolica'),

    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votsimbbloco/$',
            VotacaoView.as_view(), name='votacaosimbolicabloco'),

    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/votsimb/view/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoEditView.as_view(), name='votacaosimbolicaedit'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votnom/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalExpedienteView.as_view(), name='votacaonominalexp'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votnom/edit/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalExpedienteEditView.as_view(),
            name='votacaonominalexpedit'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votnom/detail/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalExpedienteDetailView.as_view(),
            name='votacaonominalexpdetail'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votsimb/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoExpedienteView.as_view(), name='votacaosimbolicaexp'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votsimb/view/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoExpedienteEditView.as_view(), name='votacaosimbolicaexpedit'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votsec/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoExpedienteView.as_view(), name='votacaosecretaexp'),
    re_path(r'^sessao/(?P<pk>\d+)/matexp/votsec/view/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoExpedienteEditView.as_view(), name='votacaosecretaexpedit'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao-nominal-transparencia/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoNominalTransparenciaDetailView.as_view(),
            name='votacao_nominal_transparencia'),
    re_path(r'^sessao/(?P<pk>\d+)/votacao-simbolica-transparencia/(?P<oid>\d+)/(?P<mid>\d+)$',
            VotacaoSimbolicaTransparenciaDetailView.as_view(),
            name='votacao_simbolica_transparencia'),
    re_path(r'^sessao/mudar-ordem-materia-sessao/',
            mudar_ordem_materia_sessao,
            name='mudar_ordem_materia_sessao'),

    re_path(r'^sessao/votacao-nominal-parlamentar/',
            voto_nominal_parlamentar,
            name='votacao_nominal_parlamentar'
            ),


    re_path(r'^sessao/(?P<pk>\d+)/matexp/leitura/(?P<oid>\d+)/(?P<mid>\d+)$',
            ExpedienteLeituraView.as_view(), name='leituraexp'),
    re_path(r'^sessao/(?P<pk>\d+)/matordemdia/leitura/(?P<oid>\d+)/(?P<mid>\d+)$',
            OrdemDiaLeituraView.as_view(), name='leituraod'),

    re_path(r'^sessao/(?P<pk>\d+)/(?P<iso>\d+)/(?P<oid>\d+)/retirar-leitura$',
            retirar_leitura, name='retirar_leitura'),

    re_path(r'^sessao/votacoes', RegistroVotacaoFilterView.as_view(), name='votacoes_pesquisa'),

]
