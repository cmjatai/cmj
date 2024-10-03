from django.urls.conf import re_path, include

from sapl.parlamentares.views import (CargoMesaCrud, ColigacaoCrud,
                                      ComposicaoColigacaoCrud, DependenteCrud,
                                      BancadaCrud, CargoBancadaCrud,
                                      FiliacaoCrud, FrenteCrud, FrenteList,
                                      LegislaturaCrud, MandatoCrud,
                                      MesaDiretoraView, NivelInstrucaoCrud,
                                      ParlamentarCrud, ParlamentarMateriasView,
                                      ParticipacaoParlamentarCrud, PartidoCrud,
                                      ProposicaoParlamentarCrud,
                                      RelatoriaParlamentarCrud,
                                      SessaoLegislativaCrud,
                                      TipoAfastamentoCrud, TipoDependenteCrud,
                                      AfastamentoParlamentarCrud,
                                      TipoMilitarCrud, VotanteView,
                                      altera_field_mesa,
                                      altera_field_mesa_public_view,
                                      frente_atualiza_lista_parlamentares,
                                      insere_parlamentar_composicao,
                                      parlamentares_frente_selected,
                                      remove_parlamentar_composicao,
                                      lista_parlamentares,
                                      parlamentares_filiados,
                                      BlocoCrud, CargoBlocoCrud,
                                      PesquisarParlamentarView,
                                      VincularParlamentarView,
                                      deleta_historico_partido,
                                      edita_vinculo_parlamentar_bloco,
                                      deleta_vinculo_parlamentar_bloco,
                                      vincula_parlamentar_ao_bloco,
                                      get_sessoes_legislatura)


from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(r'^parl', include(
        ParlamentarCrud.get_urls() + DependenteCrud.get_urls() +
        FiliacaoCrud.get_urls() + MandatoCrud.get_urls() +
        ParticipacaoParlamentarCrud.get_urls() +
        ProposicaoParlamentarCrud.get_urls() +
        RelatoriaParlamentarCrud.get_urls() + FrenteList.get_urls() +
        VotanteView.get_urls() + AfastamentoParlamentarCrud.get_urls() +
        BancadaCrud.get_urls()
    )),

    re_path(r'^parlamentar/bancada', include(
        BancadaCrud.get_urls()
    )),

    re_path(r'^parlamentar/bloco', include(
        BlocoCrud.get_urls()
    )),

    re_path(r'^parlamentar/lista$', lista_parlamentares, name='lista_parlamentares'),

    re_path(r'^parlamentar/pesquisar-parlamentar/',
        PesquisarParlamentarView.as_view(), name='pesquisar_parlamentar'),

    re_path(r'^parlamentar/deleta_partido/(?P<pk>\d+)/$',
        deleta_historico_partido, name='deleta_historico_partido'),

    re_path(r'^parlamentar/(?P<pk>\d+)/materias$',
        ParlamentarMateriasView.as_view(), name='parlamentar_materias'),

    re_path(r'^parlamentar/vincular-parlamentar/$',
        VincularParlamentarView.as_view(), name='vincular_parlamentar'),

    re_path(r'^sistema/coligacao',
        include(ColigacaoCrud.get_urls() +
                ComposicaoColigacaoCrud.get_urls())),

    re_path(r'^sistema/cargo-bancada',
        include(CargoBancadaCrud.get_urls())),

    re_path(r'^sistema/cargo-bloco',
        include(CargoBlocoCrud.get_urls())),
    re_path(r'^sistema/vincula-parlamentar-ao-bloco/(?P<pk>\d+)/',
        vincula_parlamentar_ao_bloco, name='vincula_parlamentar_ao_bloco'),
    re_path(r'^sistema/edita-vinculo-parlamentar-bloco/(?P<pk>\d+)/',
        edita_vinculo_parlamentar_bloco, name='edita-vinculo-parlamentar-bloco'),
    re_path(r'^sistema/deleta-vinculo-parlamentar-bloco/(?P<pk>\d+)/',
        deleta_vinculo_parlamentar_bloco, name='deleta-vinculo-parlamentar-bloco'),

    re_path(r'^sistema/frente',
        include(FrenteCrud.get_urls())),
    re_path(r'^sistema/frente/atualiza-lista-parlamentares',
        frente_atualiza_lista_parlamentares,
        name='atualiza_lista_parlamentares'),
    re_path(r'^sistema/frente/parlamentares-frente-selected',
        parlamentares_frente_selected,
        name='parlamentares_frente_selected'),

    re_path(r'^sistema/parlamentar/legislatura',
        include(LegislaturaCrud.get_urls())),
    re_path(r'^sistema/parlamentar/tipo-dependente',
        include(TipoDependenteCrud.get_urls())),
    re_path(r'^sistema/parlamentar/nivel-instrucao',
        include(NivelInstrucaoCrud.get_urls())),
    re_path(r'^sistema/parlamentar/tipo-afastamento',
        include(TipoAfastamentoCrud.get_urls())),
    re_path(r'^sistema/parlamentar/tipo-militar',
        include(TipoMilitarCrud.get_urls())),
    re_path(r'^sistema/parlamentar/partido', include(PartidoCrud.get_urls())),

    re_path(r'^sistema/parlamentar/partido/(?P<pk>\d+)/filiados$',
        parlamentares_filiados, name='parlamentares_filiados'),

    re_path(r'^sistema/mesa-diretora/sessao-legislativa',
        include(SessaoLegislativaCrud.get_urls())),
    re_path(r'^sistema/mesa-diretora/cargo-mesa',
        include(CargoMesaCrud.get_urls())),

    re_path(r'^mesa-diretora/$',
        MesaDiretoraView.as_view(), name='mesa_diretora'),

    re_path(r'^mesa-diretora/altera-field-mesa/$',
        altera_field_mesa, name='altera_field_mesa'),

    re_path(r'^mesa-diretora/altera-field-mesa-public-view/$',
        altera_field_mesa_public_view, name='altera_field_mesa_public_view'),

    re_path(r'^mesa-diretora/insere-parlamentar-composicao/$',
        insere_parlamentar_composicao, name='insere_parlamentar_composicao'),

    re_path(r'^mesa-diretora/remove-parlamentar-composicao/$',
        remove_parlamentar_composicao, name='remove_parlamentar_composicao'),

    re_path(r'^parlamentar/get-sessoes-legislatura/$',
        get_sessoes_legislatura, name='get_sessoes_legislatura'),

]
