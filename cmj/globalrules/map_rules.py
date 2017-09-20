from django.contrib.auth import get_user_model
from sapl.parlamentares.models import Partido

from cmj.cerimonial.models import Perfil, EnderecoPerfil, EmailPerfil,\
    TelefonePerfil, LocalTrabalhoPerfil, DependentePerfil, OperadoraTelefonia,\
    NivelInstrucao, EstadoCivil, Contato, FiliacaoPartidaria, Dependente,\
    LocalTrabalho, Telefone, Email, Endereco, GrupoDeContatos, ProcessoContato,\
    Processo, AssuntoProcesso
from cmj.core.models import Trecho
from cmj.globalrules import (RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL, RP_LIST,
                             GROUP_SOCIAL_USERS, GROUP_SAAP_WORKSPACE_OPER_CONTATOS,
                             menu_contatos, menu_dados_auxiliares,
                             menu_grupocontatos, menu_relatorios,
                             GROUP_SAAP_WORKSPACE_MANAGERS,
                             GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
                             GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
                             menu_processos, GROUP_ANONYMOUS)


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
            menu_grupocontatos,
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
# não possui efeito e é usada nos testes que verificam se todos os models estão
# neste arquivo rules.py
rules_group_anonymous = {
    'group': GROUP_ANONYMOUS,
    'rules': []
}

rules_patterns = [
    rules_group_social_users,
    rules_group_anonymous,
    rules_saap_group_workspace_managers,
    rules_saap_group_workspace_oper_contatos,
    rules_saap_group_workspace_oper_grupo_contatos,
    rules_saap_group_workspace_oper_processos
]
