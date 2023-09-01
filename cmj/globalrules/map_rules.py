from django.contrib.auth import get_user_model

from cmj.agenda.models import Evento
from cmj.arq.models import Draft, DraftMidia
from cmj.cerimonial.models import Perfil, EnderecoPerfil, EmailPerfil,\
    TelefonePerfil, LocalTrabalhoPerfil, DependentePerfil, OperadoraTelefonia,\
    NivelInstrucao, EstadoCivil, Contato, FiliacaoPartidaria, Dependente,\
    LocalTrabalho, Telefone, Email, Endereco, GrupoDeContatos, ProcessoContato,\
    Processo, AssuntoProcesso, TipoTelefone, TipoEmail, Parentesco,\
    PronomeTratamento, TipoAutoridade, TipoEndereco, TipoLocalTrabalho,\
    StatusProcesso, ClassificacaoProcesso, TopicoProcesso, Visita, Visitante
from cmj.core.models import Trecho, Municipio, AreaTrabalho,\
    OperadorAreaTrabalho, Cep, RegiaoMunicipal, Bairro, TipoLogradouro,\
    Distrito, Logradouro, ImpressoEnderecamento, Notificacao
from cmj.diarios.models import DiarioOficial, TipoDeDiario,\
    VinculoDocDiarioOficial
from cmj.globalrules import (RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL, RP_LIST,
                             GROUP_SOCIAL_USERS,
                             GROUP_SAAP_WORKSPACE_OPER_CONTATOS,
                             menu_contatos, menu_dados_auxiliares,
                             menu_grupocontatos, menu_relatorios,
                             GROUP_SAAP_WORKSPACE_MANAGERS,
                             GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
                             GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
                             menu_processos, GROUP_ANONYMOUS, GROUP_ADMIN,
                             menu_impresso_enderecamento,
                             menu_tabelas_auxiliares,
                             menu_administracao,
                             GROUP_SIGAD_VIEW_STATUS_RESTRITOS,
                             GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
                             GROUP_AGENDA_WORKSPACE, menu_agenda,
                             GROUP_MATERIA_WORKSPACE_VIEWER,
                             GROUP_DIARIOS_OPERADOR,
                             GROUP_SAAP_WORKSPACE_OPER_RECEPCAO, menu_recepcao,
                             GROUP_DRAFT_OPERADOR)
from cmj.ouvidoria.models import Solicitacao, MensagemSolicitacao
from cmj.sigad.models import Classe, Documento, Midia
from sapl.parlamentares.models import Partido
from sapl.rules import SAPL_GROUP_GERAL
from sapl.rules.map_rules import __base__


__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]


rules_group_social_users = {
    'group': GROUP_SOCIAL_USERS,
    'rules': [
        (Perfil, __base__),
        (EnderecoPerfil, __base__),
        (EmailPerfil, __base__),
        (TelefonePerfil, __base__),
        (LocalTrabalhoPerfil, __base__),
        (DependentePerfil, __base__),
    ]
}

rules_group_admin = {
    'group': GROUP_ADMIN,
    'rules': [
        (get_user_model(), __base__ + [
            menu_impresso_enderecamento,
            menu_tabelas_auxiliares,
            menu_administracao,
        ]),
        (Municipio, __base__),
        (AreaTrabalho, __base__),
        (OperadorAreaTrabalho, __base__),
        (Cep, __base__),
        (RegiaoMunicipal, __base__),
        (Bairro, __base__),
        (TipoLogradouro, __base__),
        (Distrito, __base__),
        (Logradouro, __base__),
        (Trecho, __base__),
        (ImpressoEnderecamento, __base__),
        (TipoTelefone, __base__),
        (TipoEndereco, __base__),
        (TipoEmail, __base__),
        (Parentesco, __base__),
        (EstadoCivil, __base__),
        (PronomeTratamento, __base__),
        (TipoAutoridade, __base__),
        (TipoLocalTrabalho, __base__),
        (NivelInstrucao, __base__),
        (OperadoraTelefonia, __base__),
        (StatusProcesso, __base__),
        (ClassificacaoProcesso, __base__),
        (TopicoProcesso, __base__),

    ]
}


rules_saap_group_workspace_managers = {
    'group': GROUP_SAAP_WORKSPACE_MANAGERS,
    'rules': []
}


rules_saap_group_workspace_oper_contatos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_CONTATOS,
    'rules': [
        (get_user_model(), [
            menu_contatos,
            menu_dados_auxiliares,
            menu_relatorios]),
        (Trecho, [RP_LIST, RP_DETAIL]),
        (OperadoraTelefonia, [RP_LIST, RP_DETAIL]),
        (NivelInstrucao, [RP_LIST, RP_DETAIL]),
        (EstadoCivil, [RP_LIST, RP_DETAIL]),
        (Partido, [RP_LIST, RP_DETAIL]),
        (Contato, __base__ + [
            'print_impressoenderecamento',
            'print_rel_contato_agrupado_por_processo',
            'print_rel_contato_agrupado_por_grupo']),
        (Endereco, __base__),
        (Email, __base__),
        (Telefone, __base__),
        (LocalTrabalho, __base__),
        (Dependente, __base__),
        (FiliacaoPartidaria, __base__),
    ]
}


rules_saap_group_workspace_oper_grupo_contatos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
    'rules': [
        (get_user_model(), [
            menu_contatos,
            menu_grupocontatos, ]),
        (GrupoDeContatos, __base__),
        (Contato, [RP_LIST, RP_DETAIL, ]),
    ]
}

rules_saap_group_workspace_oper_recepcao = {
    'group': GROUP_SAAP_WORKSPACE_OPER_RECEPCAO,
    'rules': [
        (get_user_model(), [
            menu_recepcao, ]),
        (Visita, [RP_LIST, RP_DETAIL, RP_ADD, ]),
        (Visitante, [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, ]),
    ]
}

rules_saap_group_workspace_oper_processos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
    'rules': [
        (get_user_model(), [
            menu_processos,
            menu_dados_auxiliares,
            menu_relatorios]),
        (AssuntoProcesso, __base__),
        (Processo, __base__),
        (ProcessoContato, __base__),
    ]
}

rules_materia_group_workspace = {
    'group': GROUP_MATERIA_WORKSPACE_VIEWER,
    'rules': []
}


rules_agenda_group_workspace = {
    'group': GROUP_AGENDA_WORKSPACE,
    'rules': [
        (get_user_model(), [
            menu_dados_auxiliares,
            menu_agenda]),
        (Evento, __base__)
    ]
}


rules_diarios_group_operador = {
    'group': GROUP_DIARIOS_OPERADOR,
    'rules': [
        (DiarioOficial, __base__),
        (VinculoDocDiarioOficial, __base__)
    ]
}

rules_draft_group_operador = {
    'group': GROUP_DRAFT_OPERADOR,
    'rules': [
        (Draft, __base__),
        (DraftMidia, __base__),
    ]
}


"""
rules_group_geral = {
    'group': SAPL_GROUP_GERAL,
    'rules': [
        (TipoDeDiario, __base__)
    ]
}
"""
# não possui efeito e é usada nos testes que verificam se todos os models estão
# neste arquivo rules.py
rules_group_anonymous = {
    'group': GROUP_ANONYMOUS,
    'rules': []
}

rules_sigad_view_status_restritos = {
    'group': GROUP_SIGAD_VIEW_STATUS_RESTRITOS,
    'rules': [
        (get_user_model(), ['menu_dados_auxiliares']),
        (Midia, [RP_DETAIL]),
        (Classe, [
            'view_pathclasse',
            'view_subclasse',
        ]),

        (Documento, [
            'view_documento_show'
        ])]
}

rules_ouvidoria_visualizacao_respostas = {
    'group': GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
    'rules': [

        (Solicitacao, [RP_LIST, RP_DETAIL]),
        (Notificacao, ['popup_notificacao']),
        (MensagemSolicitacao, [RP_DETAIL])
    ]
}


rules_patterns = [
    rules_group_admin,
    rules_group_social_users,
    rules_group_anonymous,
    rules_saap_group_workspace_managers,
    rules_saap_group_workspace_oper_contatos,
    rules_saap_group_workspace_oper_grupo_contatos,
    rules_saap_group_workspace_oper_recepcao,
    rules_saap_group_workspace_oper_processos,
    rules_agenda_group_workspace,
    rules_materia_group_workspace,

    rules_diarios_group_operador,
    rules_draft_group_operador,

    rules_sigad_view_status_restritos,
    rules_ouvidoria_visualizacao_respostas,

    # rules_group_geral
]
