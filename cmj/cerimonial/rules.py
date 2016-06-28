from django.contrib.auth import get_user_model

from cmj.cerimonial.models import Perfil, Endereco, Email, Telefone,\
    LocalTrabalho, Dependente, Contato, EnderecoPerfil, EmailPerfil,\
    TelefonePerfil, LocalTrabalhoPerfil, DependentePerfil, OperadoraTelefonia,\
    NivelInstrucao
from cmj.core.models import User, Trecho
from cmj.core.rules import menu_contatos, menu_dados_auxiliares, search_trecho
from cmj.globalrules.crud_custom import LIST, ADD, DETAIL, CHANGE, DELETE
from cmj.globalrules.globalrules import GROUP_SOCIAL_USERS,\
    GROUP_WORKSPACE_OPER_CONTATOS, GROUP_WORKSPACE_MANAGERS


rules_group_social_users = (
    GROUP_SOCIAL_USERS, [
        (Perfil, [ADD, DETAIL, CHANGE, DELETE]),
        (EnderecoPerfil, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (EmailPerfil, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (TelefonePerfil, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (LocalTrabalhoPerfil, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (DependentePerfil, [LIST, ADD, DETAIL, CHANGE, DELETE]), ])

rules_group_workspace_managers = (
    GROUP_WORKSPACE_MANAGERS, [
    ]
)

rules_group_workspace_oper_contatos = (
    GROUP_WORKSPACE_OPER_CONTATOS, [
        (get_user_model(), [menu_contatos, menu_dados_auxiliares]),
        (Trecho, [search_trecho]),
        (OperadoraTelefonia, [LIST, DETAIL]),
        (NivelInstrucao, [LIST, DETAIL]),
        (Contato, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (Endereco, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (Email, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (Telefone, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (LocalTrabalho, [LIST, ADD, DETAIL, CHANGE, DELETE]),
        (Dependente, [LIST, ADD, DETAIL, CHANGE, DELETE]),
    ]
)

rules_patterns = [
    rules_group_social_users,
    rules_group_workspace_managers,
    rules_group_workspace_oper_contatos,
]
