from django.contrib.auth import get_user_model
from sapl.parlamentares.models import Partido
from sapl.rules import map_rules

from cmj.cerimonial.models import Perfil, Endereco, Email, Telefone,\
    LocalTrabalho, Dependente, Contato, EnderecoPerfil, EmailPerfil,\
    TelefonePerfil, LocalTrabalhoPerfil, DependentePerfil, OperadoraTelefonia,\
    NivelInstrucao, EstadoCivil, FiliacaoPartidaria, AssuntoProcesso, Processo,\
    ProcessoContato, GrupoDeContatos
from cmj.core.models import Trecho
from cmj.core.rules import menu_contatos, menu_dados_auxiliares, search_trecho,\
    menu_processos, menu_relatorios, menu_grupocontatos
from cmj.globalrules.globalrules import GROUP_SOCIAL_USERS,\
    GROUP_WORKSPACE_OPER_CONTATOS, GROUP_WORKSPACE_MANAGERS,\
    GROUP_WORKSPACE_OPER_PROCESSOS, GROUP_WORKSPACE_OPER_GRUPO_CONTATOS


rules_group_social_users = (
    GROUP_SOCIAL_USERS, [
        (Perfil, map_rules.__base__),
        (EnderecoPerfil, map_rules.__base__),
        (EmailPerfil, map_rules.__base__),
        (TelefonePerfil, map_rules.__base__),
        (LocalTrabalhoPerfil, map_rules.__base__),
        (DependentePerfil, map_rules.__base__), ])

rules_group_workspace_managers = (
    GROUP_WORKSPACE_MANAGERS, [
    ]
)

rules_group_workspace_oper_contatos = (
    GROUP_WORKSPACE_OPER_CONTATOS, [
        (get_user_model(), [
            menu_contatos,
            menu_dados_auxiliares,
            menu_grupocontatos,
            menu_relatorios]),
        (Trecho, [map_rules.RP_LIST, map_rules.RP_DETAIL]),
        (OperadoraTelefonia, [map_rules.RP_LIST, map_rules.RP_DETAIL]),
        (NivelInstrucao, [map_rules.RP_LIST, map_rules.RP_DETAIL]),
        (EstadoCivil, [map_rules.RP_LIST, map_rules.RP_DETAIL]),
        (Partido, [map_rules.RP_LIST, map_rules.RP_DETAIL]),
        (Contato, map_rules.__base__ + [
            'print_impressoenderecamento',
            'print_rel_contato_agrupado_por_processo',
            'print_rel_contato_agrupado_por_grupo']),
        (Endereco, map_rules.__base__),
        (Email, map_rules.__base__),
        (Telefone, map_rules.__base__),
        (LocalTrabalho, map_rules.__base__),
        (Dependente, map_rules.__base__),
        (FiliacaoPartidaria, map_rules.__base__),
    ]
)

rules_group_workspace_oper_grupo_contatos = (
    GROUP_WORKSPACE_OPER_GRUPO_CONTATOS, [
        (get_user_model(), [
            menu_contatos,
            menu_grupocontatos, ]),
        (GrupoDeContatos, map_rules.__base__),
        (Contato, [map_rules.RP_LIST, map_rules.RP_DETAIL, ]),
    ]
)
rules_group_workspace_oper_processos = (
    GROUP_WORKSPACE_OPER_PROCESSOS, [
        (get_user_model(), [
            menu_processos,
            menu_dados_auxiliares,
            menu_relatorios]),
        (AssuntoProcesso, map_rules.__base__),
        (Processo, map_rules.__base__),
        (ProcessoContato, map_rules.__base__),
    ]
)
rules_patterns = [
    rules_group_social_users,
    rules_group_workspace_managers,
    rules_group_workspace_oper_contatos,
    rules_group_workspace_oper_grupo_contatos,
    rules_group_workspace_oper_processos,
]
