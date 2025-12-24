from django.contrib.auth import get_user_model
from cmj import loa
from cmj.agenda import models as agenda_models
from cmj.arq import models as arq_models
from cmj.diarios import models as diarios_models
from cmj.loa import models as loa_models
from cmj.ouvidoria import models as ouvidoria_models
from cmj.painelset import models as painelset_models
from cmj.sigad import models as sigad_models
from cmj.cerimonial import models as cerimonial_models
from cmj.core import models as core_models
from sapl.parlamentares import models as parlamentares_models
from cmj.search import models as search_models
from cmj.globalrules import (GROUP_IA_OPERADOR, GROUP_PAINELSET_OPERADOR, RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL, RP_LIST,
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

from sapl.rules import SAPL_GROUP_GERAL
from sapl.rules.map_rules import __base__


__base__ = [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE]
__listdetailchange__ = [RP_LIST, RP_DETAIL, RP_CHANGE]

__perms_publicas__ = {RP_LIST, RP_DETAIL}


rules_group_social_users = {
    'group': GROUP_SOCIAL_USERS,
    'rules': [
        (cerimonial_models.Perfil, __base__, set()),
        (cerimonial_models.EnderecoPerfil, __base__, set()),
        (cerimonial_models.EmailPerfil, __base__, set()),
        (cerimonial_models.TelefonePerfil, __base__, set()),
        (cerimonial_models.LocalTrabalhoPerfil, __base__, set()),
        (cerimonial_models.DependentePerfil, __base__, set()),
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
        (core_models.Municipio, __base__, set()),
        (core_models.AreaTrabalho, __base__, set()),
        (core_models.OperadorAreaTrabalho, __base__, set()),
        (core_models.Cep, __base__, set()),
        (core_models.RegiaoMunicipal, __base__, set()),
        (core_models.Bairro, __base__, set()),
        (core_models.TipoLogradouro, __base__, set()),
        (core_models.Distrito, __base__, set()),
        (core_models.Logradouro, __base__, set()),
        (core_models.Trecho, __base__, set()),
        (core_models.ImpressoEnderecamento, __base__, set()),
        (cerimonial_models.TipoTelefone, __base__, set()),
        (cerimonial_models.TipoEndereco, __base__, set()),
        (cerimonial_models.TipoEmail, __base__, set()),
        (cerimonial_models.Parentesco, __base__, set()),
        (cerimonial_models.EstadoCivil, __base__, set()),
        (cerimonial_models.PronomeTratamento, __base__, set()),
        (cerimonial_models.TipoAutoridade, __base__, set()),
        (cerimonial_models.TipoLocalTrabalho, __base__, set()),
        (cerimonial_models.NivelInstrucao, __base__, set()),
        (cerimonial_models.OperadoraTelefonia, __base__, set()),
        (cerimonial_models.StatusProcesso, __base__, set()),
        (cerimonial_models.ClassificacaoProcesso, __base__, set()),
        (cerimonial_models.TopicoProcesso, __base__, set()),

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
        (core_models.Trecho, [RP_LIST, RP_DETAIL], set()),
        (cerimonial_models.OperadoraTelefonia, [RP_LIST, RP_DETAIL], set()),
        (cerimonial_models.NivelInstrucao, [RP_LIST, RP_DETAIL], set()),
        (cerimonial_models.EstadoCivil, [RP_LIST, RP_DETAIL], set()),
        (parlamentares_models.Partido, [RP_LIST, RP_DETAIL], set()),
        (cerimonial_models.Contato, __base__ + [
            'print_impressoenderecamento',
            'print_rel_contato_agrupado_por_processo',
            'print_rel_contato_agrupado_por_grupo'], set()),
        (cerimonial_models.Endereco, __base__, set()),
        (cerimonial_models.Email, __base__, set()),
        (cerimonial_models.Telefone, __base__, set()),
        (cerimonial_models.LocalTrabalho, __base__, set()),
        (cerimonial_models.Dependente, __base__, set()),
        (cerimonial_models.FiliacaoPartidaria, __base__, set()),
    ]
}


rules_saap_group_workspace_oper_grupo_contatos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_GRUPO_CONTATOS,
    'rules': [
        (get_user_model(), [
            menu_contatos,
            menu_grupocontatos, ], set()),
        (cerimonial_models.GrupoDeContatos, __base__, set()),
        (cerimonial_models.Contato, [RP_LIST, RP_DETAIL, ], set()),
    ]
}

rules_saap_group_workspace_oper_recepcao = {
    'group': GROUP_SAAP_WORKSPACE_OPER_RECEPCAO,
    'rules': [
        (get_user_model(), [
            menu_recepcao, ], set()),
        (cerimonial_models.Visita, [RP_LIST, RP_DETAIL, RP_ADD, ], set()),
        (cerimonial_models.Visitante, [RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, ], set()),
    ]
}

rules_saap_group_workspace_oper_processos = {
    'group': GROUP_SAAP_WORKSPACE_OPER_PROCESSOS,
    'rules': [
        (get_user_model(), [
            menu_processos,
            menu_dados_auxiliares,
            menu_relatorios], set()),
        (cerimonial_models.AssuntoProcesso, __base__, set()),
        (cerimonial_models.AnexoProcesso, __base__, set()),
        (cerimonial_models.Processo, __base__, set()),
        (cerimonial_models.ProcessoContato, __base__, set()),
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
        (agenda_models.Evento, __base__, set())
    ]
}


rules_diarios_group_operador = {
    'group': GROUP_DIARIOS_OPERADOR,
    'rules': [
        (diarios_models.DiarioOficial, __base__, __perms_publicas__),
        (diarios_models.VinculoDocDiarioOficial, __base__, __perms_publicas__)
    ]
}

rules_loa_group_operador = {
    'group': GROUP_LOA_OPERADOR,
    'rules': [
        (loa_models.Loa, __base__, set(__perms_publicas__)),
        (loa_models.LoaParlamentar, __base__, __perms_publicas__),
        (loa_models.EmendaLoa, __base__ + ['emendaloa_full_editor'], __perms_publicas__),
        (loa_models.EmendaLoaParlamentar, __base__, __perms_publicas__),
        (loa_models.OficioAjusteLoa, __base__, __perms_publicas__),
        (loa_models.RegistroAjusteLoa, __base__, __perms_publicas__),

        (loa_models.Entidade, __base__, __perms_publicas__),

        (loa_models.DespesaConsulta, __base__, __perms_publicas__),

        (loa_models.Orgao, __base__, __perms_publicas__),
        (loa_models.UnidadeOrcamentaria, __base__, __perms_publicas__),
        (loa_models.Funcao, __base__, __perms_publicas__),
        (loa_models.SubFuncao, __base__, __perms_publicas__),
        (loa_models.Programa, __base__, __perms_publicas__),
        (loa_models.Acao, __base__, __perms_publicas__),
        (loa_models.Natureza, __base__, __perms_publicas__),
        (loa_models.EmendaLoaRegistroContabil, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),

        (loa_models.Agrupamento, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),
        (loa_models.AgrupamentoEmendaLoa, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),
        (loa_models.AgrupamentoRegistroContabil, __base__ +
         ['emendaloa_full_editor'], __perms_publicas__),

        (loa_models.PrestacaoContaLoa, __base__, __perms_publicas__),
        (loa_models.ArquivoPrestacaoContaLoa, __base__, __perms_publicas__),
        (loa_models.PrestacaoContaRegistro, __base__, __perms_publicas__),

    ]
}

rules_draft_group_operador = {
    'group': GROUP_DRAFT_OPERADOR,
    'rules': [
        (arq_models.Draft, __base__, set()),
        (arq_models.DraftMidia, __base__, set()),
    ]
}

rules_ia_group_operador = {
    'group': GROUP_IA_OPERADOR,
    'rules': [
        (get_user_model(), [
            'search.can_use_chat_module'], set()),
        (search_models.ChatSession, __base__ + [
            'search.can_use_chat_module'
        ], set()),
        (search_models.ChatMessage, __base__+ [
            'search.can_use_chat_module'
        ], set()),
        #(search_models.Embedding, __base__, set()),
    ]
}


rules_arq_group_operador = {
    'group': GROUP_ARQ_OPERADOR,
    'rules': [
        (arq_models.Draft, __base__ + [
            'view_draft',
        ], set()),
        (arq_models.DraftMidia, __base__ + [
            'view_draftmidia',
        ], set()),
        (arq_models.ArqClasse, __base__ + [
            'view_arqclasse',
        ], set()),
        (arq_models.ArqDoc, __base__ + [
            'view_arqdoc',
        ], set()),
    ]
}

rules_painelset_group_operador = {
    'group': GROUP_PAINELSET_OPERADOR,
    'rules': [
        (painelset_models.Cronometro, __base__, __perms_publicas__),
        (painelset_models.Individuo, __base__, __perms_publicas__),
        (painelset_models.Evento, __base__, __perms_publicas__),
        (painelset_models.Painel, __base__, __perms_publicas__),
        (painelset_models.Widget, __base__, __perms_publicas__),
        (painelset_models.VisaoDePainel, __base__, __perms_publicas__),
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
        (sigad_models.Midia, [RP_DETAIL], set()),
        (sigad_models.Classe, [
            'view_pathclasse',
            'view_subclasse',
        ], set()),

        (sigad_models.Documento, [
            'view_docume'
            'nto_show'
        ], set())]
}

rules_ouvidoria_visualizacao_respostas = {
    'group': GROUP_OUVIDORIA_VISUALIZACAO_RESPOSTAS,
    'rules': [

        (ouvidoria_models.Solicitacao, [RP_LIST, RP_DETAIL], set()),
        (core_models.Notificacao, ['popup_notificacao'], set()),
        (ouvidoria_models.MensagemSolicitacao, [RP_DETAIL], set())
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

    rules_painelset_group_operador,

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
