from django.contrib.auth import get_user_model

from cmj.agenda.models import Evento
from cmj.arq.models import Draft, DraftMidia, ArqClasse, ArqDoc
from cmj.cerimonial.models import Perfil, EnderecoPerfil, EmailPerfil,\
    TelefonePerfil, LocalTrabalhoPerfil, DependentePerfil, OperadoraTelefonia,\
    NivelInstrucao, EstadoCivil, Contato, FiliacaoPartidaria, Dependente,\
    LocalTrabalho, Telefone, Email, Endereco, GrupoDeContatos, ProcessoContato,\
    Processo, AssuntoProcesso, TipoTelefone, TipoEmail, Parentesco,\
    PronomeTratamento, TipoAutoridade, TipoEndereco, TipoLocalTrabalho,\
    StatusProcesso, ClassificacaoProcesso, TopicoProcesso, Visita, Visitante, \
    AnexoProcesso
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
                             GROUP_LOA_OPERADOR,
                             GROUP_SAAP_WORKSPACE_OPER_RECEPCAO, menu_recepcao,
                             GROUP_DRAFT_OPERADOR, GROUP_ARQ_OPERADOR)
from cmj.loa.models import Entidade, Loa, LoaParlamentar, EmendaLoa, EmendaLoaParlamentar,\
    OficioAjusteLoa, RegistroAjusteLoa, DespesaConsulta, Orgao,\
    UnidadeOrcamentaria, EmendaLoaRegistroContabil, Funcao, SubFuncao, Programa,\
    Acao, Natureza, Agrupamento, AgrupamentoEmendaLoa,\
    AgrupamentoRegistroContabil
from cmj.ouvidoria.models import Solicitacao, MensagemSolicitacao
from cmj.sigad.models import Classe, Documento, Midia
from sapl.parlamentares.models import Partido
from sapl.rules import SAPL_GROUP_GERAL
from sapl.rules.map_rules import __base__


__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]

__perms_publicas__ = {RP_LIST, RP_DETAIL}


rules_group_social_users = {
    'group': GROUP_SOCIAL_USERS,
    'rules': [
        (Perfil, __base__, set()),
        (EnderecoPerfil, __base__, set()),
        (EmailPerfil, __base__, set()),
        (TelefonePerfil, __base__, set()),
        (LocalTrabalhoPerfil, __base__, set()),
        (DependentePerfil, __base__, set()),
    ]
}

rules_group_admin = {
    'group': GROUP_ADMIN,
    'rules': [
        (get_user_model(), __base__ + [
            menu_impresso_enderecamento,
            menu_tabelas_auxiliares,
            menu_administracao,
        ], set()),
        (Municipio, __base__, set()),
        (AreaTrabalho, __base__, set()),
        (OperadorAreaTrabalho, __base__, set()),
        (Cep, __base__, set()),
        (RegiaoMunicipal, __base__, set()),
        (Bairro, __base__, set()),
        (TipoLogradouro, __base__, set()),
        (Distrito, __base__, set()),
        (Logradouro, __base__, set()),
        (Trecho, __base__, set()),
        (ImpressoEnderecamento, __base__, set()),
        (TipoTelefone, __base__, set()),
        (TipoEndereco, __base__, set()),
        (TipoEmail, __base__, set()),
        (Parentesco, __base__, set()),
        (EstadoCivil, __base__, set()),
        (PronomeTratamento, __base__, set()),
        (TipoAutoridade, __base__, set()),
        (TipoLocalTrabalho, __base__, set()),
        (NivelInstrucao, __base__, set()),
        (OperadoraTelefonia, __base__, set()),
        (StatusProcesso, __base__, set()),
        (ClassificacaoProcesso, __base__, set()),
        (TopicoProcesso, __base__, set()),

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
            menu_relatorios], set()),
        (Trecho, [RP_LIST, RP_DETAIL], set()),
        (OperadoraTelefonia, [RP_LIST, RP_DETAIL], set()),
        (NivelInstrucao, [RP_LIST, RP_DETAIL], set()),
        (EstadoCivil, [RP_LIST, RP_DETAIL], set()),
        (Partido, [RP_LIST, RP_DETAIL], set()),
        (Contato, __base__ + [
            'print_impressoenderecamento',
            'print_rel_contato_agrupado_por_processo',
            'print_rel_contato_agrupado_por_grupo'], set()),
        (Endereco, __base__, set()),
        (Email, __base__, set()),
        (Telefone, __base__, set()),
        (LocalTrabalho, __base__, set()),
        (Dependente, __base__, set()),
        (FiliacaoPartidaria, __base__, set()),
    ]
}


rules_saap_group_workspace_oper_grupo_contatos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
    'rules': [
        (get_user_model(), [
            menu_contatos,
            menu_grupocontatos, ], set()),
        (GrupoDeContatos, __base__, set()),
        (Contato, [RP_LIST, RP_DETAIL, ], set()),
    ]
}

rules_saap_group_workspace_oper_recepcao = {
    'group': GROUP_SAAP_WORKSPACE_OPER_RECEPCAO,
    'rules': [
        (get_user_model(), [
            menu_recepcao, ], set()),
        (Visita, [RP_LIST, RP_DETAIL, RP_ADD, ], set()),
        (Visitante, [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, ], set()),
    ]
}

rules_saap_group_workspace_oper_processos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
    'rules': [
        (get_user_model(), [
            menu_processos,
            menu_dados_auxiliares,
            menu_relatorios], set()),
        (AssuntoProcesso, __base__, set()),
        (AnexoProcesso, __base__, set()),
        (Processo, __base__, set()),
        (ProcessoContato, __base__, set()),
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
            menu_agenda], set()),
        (Evento, __base__, set())
    ]
}


rules_diarios_group_operador = {
    'group': GROUP_DIARIOS_OPERADOR,
    'rules': [
        (DiarioOficial, __base__, __perms_publicas__),
        (VinculoDocDiarioOficial, __base__, __perms_publicas__)
    ]
}

rules_loa_group_operador = {
    'group': GROUP_LOA_OPERADOR,
    'rules': [
        (Loa, __base__, set()),
        (LoaParlamentar, __base__, __perms_publicas__),
        (EmendaLoa, __base__ + ['emendaloa_full_editor'], __perms_publicas__),
        (EmendaLoaParlamentar, __base__, __perms_publicas__),
        (OficioAjusteLoa, __base__, __perms_publicas__),
        (RegistroAjusteLoa, __base__, __perms_publicas__),

        (Entidade, __base__, __perms_publicas__),

        (DespesaConsulta, __base__, __perms_publicas__),

        (Orgao, __base__, __perms_publicas__),
        (UnidadeOrcamentaria, __base__, __perms_publicas__),
        (Funcao, __base__, __perms_publicas__),
        (SubFuncao, __base__, __perms_publicas__),
        (Programa, __base__, __perms_publicas__),
        (Acao, __base__, __perms_publicas__),
        (Natureza, __base__, __perms_publicas__),
        (EmendaLoaRegistroContabil, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),

        (Agrupamento, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),
        (AgrupamentoEmendaLoa, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),
        (AgrupamentoRegistroContabil, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),

    ]
}

rules_draft_group_operador = {
    'group': GROUP_DRAFT_OPERADOR,
    'rules': [
        (Draft, __base__, set()),
        (DraftMidia, __base__, set()),
    ]
}


rules_arq_group_operador = {
    'group': GROUP_ARQ_OPERADOR,
    'rules': [
        (Draft, __base__ + [
            'view_draft',
        ], set()),
        (DraftMidia, __base__ + [
            'view_draftmidia',
        ], set()),
        (ArqClasse, __base__ + [
            'view_arqclasse',
        ], set()),
        (ArqDoc, __base__ + [
            'view_arqdoc',
        ], set()),
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
        (get_user_model(), ['menu_dados_auxiliares'], set()),
        (Midia, [RP_DETAIL], set()),
        (Classe, [
            'view_pathclasse',
            'view_subclasse',
        ], set()),

        (Documento, [
            'view_documento_show'
        ], set())]
}

rules_ouvidoria_visualizacao_respostas = {
    'group': GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
    'rules': [

        (Solicitacao, [RP_LIST, RP_DETAIL], set()),
        (Notificacao, ['popup_notificacao'], set()),
        (MensagemSolicitacao, [RP_DETAIL], set())
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
    rules_arq_group_operador,
    rules_loa_group_operador,
    rules_sigad_view_status_restritos,
    rules_ouvidoria_visualizacao_respostas,

    # rules_group_geral
]


rules_patterns_public = {}


def _get_registration_key(model):
    return '%s:%s' % (model._meta.app_label, model._meta.model_name)


for rules_group in rules_patterns:
    # print(rules_group['group'])
    for rules in rules_group['rules']:
        # print(rules)
        key = _get_registration_key(rules[0])
        if key not in rules_patterns_public:
            rules_patterns_public[key] = set()

        r = set(map(lambda x, m=rules[0]: '{}{}{}'.format(
            m._meta.app_label,
            x,
            m._meta.model_name), rules[2]))
        rules_patterns_public[key] = rules_patterns_public[key] | r
