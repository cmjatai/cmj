from django.utils.translation import gettext_lazy as _
from sapl.rules import SAPL_GROUP_ADMINISTRATIVO, SAPL_GROUP_PROTOCOLO

default_app_config = 'cmj.globalrules.apps.AppConfig'


RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE =\
    '.list_', '.detail_', '.add_', '.change_', '.delete_',


GROUP_SOCIAL_USERS = _('Usuários com Login Social')

GROUP_SAAP_WORKSPACE_OPER_RECEPCAO = _(
    'Área de Trabalho - Operadores da Recepção')
GROUP_SAAP_WORKSPACE_OPER_CONTATOS = _(
    'Área de Trabalho - Operadores de Contatos')
GROUP_SAAP_WORKSPACE_OPER_PROCESSOS = _(
    'Área de Trabalho - Operadores de Processos')
GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS = _(
    'Área de Trabalho - Operadores de Grupos de Contatos')
GROUP_SAAP_WORKSPACE_MANAGERS = _(
    'Área de Trabalho - Gestores')

GROUP_ADMIN = _('Administrador do Sistema')

GROUP_SIGAD_VIEW_STATUS_RESTRITOS = _(
    'Sigad - Visualização de itens com Status de Restrito')

GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS = _(
    'Ouvidoria - Visualização e resposta de Solicitações')


GROUP_AGENDA_WORKSPACE = _(
    'Área de Trabalho - Agenda - Manutenção da Agenda')

GROUP_MATERIA_WORKSPACE_VIEWER = _(
    'Área de Trabalho - Visualização de Matérias Legislativas sem Despacho')

GROUP_DIARIOS_OPERADOR = _('Operador dos Diários Oficiais')

GROUP_LOA_OPERADOR = _('Operador da LOA')

GROUP_DRAFT_OPERADOR = _('Usuário do Draft')

GROUP_ARQ_OPERADOR = _('Operador do Modulo Arq')

GROUP_PAINELSET_OPERADOR = _('Operador do Modulo PainelSet')

GROUP_IA_OPERADOR = _('Usuário do Chat I.A.')

GROUP_ANONYMOUS = ''

CMJ_GROUPS = [
    GROUP_ADMIN,
    GROUP_SOCIAL_USERS,
    GROUP_SAAP_WORKSPACE_OPER_CONTATOS,
    GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
    GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
    GROUP_SAAP_WORKSPACE_OPER_RECEPCAO,
    GROUP_MATERIA_WORKSPACE_VIEWER,
    GROUP_ANONYMOUS,
    GROUP_SIGAD_VIEW_STATUS_RESTRITOS,
    GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
    GROUP_DIARIOS_OPERADOR,
    GROUP_LOA_OPERADOR,
    GROUP_DRAFT_OPERADOR,
    GROUP_ARQ_OPERADOR,
    GROUP_PAINELSET_OPERADOR,
]

WORKSPACE_GROUPS = [
    GROUP_SAAP_WORKSPACE_OPER_CONTATOS,
    GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
    GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
    GROUP_SAAP_WORKSPACE_MANAGERS,
    GROUP_MATERIA_WORKSPACE_VIEWER,
    GROUP_AGENDA_WORKSPACE,
    GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
    SAPL_GROUP_ADMINISTRATIVO,
    SAPL_GROUP_PROTOCOLO,
]


menu_dados_auxiliares = "menu_dados_auxiliares"
menu_tabelas_auxiliares = "menu_tabelas_auxiliares"
menu_area_trabalho = "menu_area_trabalho"
menu_recepcao = "menu_recepcao"
menu_contatos = "menu_contatos"
menu_grupocontatos = "menu_grupocontatos"
menu_processos = "menu_processos"
menu_impresso_enderecamento = "menu_impresso_enderecamento"
menu_relatorios = "menu_relatorios"
menu_administracao = "menu_administracao"
menu_agenda = "menu_agenda"
generate_analise_genia = "generate_analise_genia"

PERMS_FOR_USERS = (
    (menu_dados_auxiliares, _('Mostrar Menu Dados Auxiliares')),
    (menu_tabelas_auxiliares, _('Mostrar Menu de Tabelas Auxiliares')),
    (menu_recepcao, _('Mostrar Menu de Registro de Entradas')),
    (menu_contatos, _('Mostrar Menu de Cadastro de Contatos')),
    (menu_grupocontatos, _('Mostrar Menu de Cadastro de Grupos de Contatos')),
    (menu_processos, _('Mostrar Menu de Cadastro de Processos')),
    (menu_area_trabalho, _('Mostrar Menu de Áreas de Trabalho')),
    (menu_impresso_enderecamento,
     _('Mostrar Menu de Impressos de Endereçamento')),
    (menu_relatorios,
     _('Mostrar Menu de Relatórios')),
    (menu_administracao, _('Mostrar Menu de Administração')),
    (menu_agenda, _('Mostrar Menu da Agenda de Eventos')),
    (generate_analise_genia, _('Gerar Análise I.A.')),
)
