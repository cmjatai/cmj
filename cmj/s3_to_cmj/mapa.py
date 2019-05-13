from sapl.audiencia.models import AnexoAudienciaPublica, AudienciaPublica, TipoAudienciaPublica
from sapl.base.models import AppConfig, Autor, CasaLegislativa, TipoAutor
from sapl.comissoes.models import CargoComissao, Comissao, Composicao, Participacao, Periodo, Reuniao, TipoComissao
from sapl.comissoes.models import DocumentoAcessorio as ComissoesDocumentoAcessorio
from sapl.compilacao.models import Dispositivo, Nota, PerfilEstruturalTextoArticulado, Publicacao, TextoArticulado, TipoDispositivo, TipoDispositivoRelationship, TipoNota, TipoPublicacao, TipoTextoArticulado, TipoVide, VeiculoPublicacao, Vide
from sapl.lexml.models import LexmlProvedor, LexmlPublicador
from sapl.materia.models import AcompanhamentoMateria, Anexada, AssuntoMateria, Autoria, DespachoInicial, DocumentoAcessorio, MateriaAssunto, MateriaLegislativa, Numeracao, Orgao, Origem, Parecer, Proposicao, RegimeTramitacao, Relatoria, StatusTramitacao, TipoDocumento, TipoFimRelatoria, TipoMateriaLegislativa, TipoProposicao, Tramitacao, UnidadeTramitacao
from sapl.norma.models import AnexoNormaJuridica, AssuntoNorma, AutoriaNorma, LegislacaoCitada, NormaJuridica, NormaRelacionada, TipoNormaJuridica, TipoVinculoNormaJuridica
from sapl.painel.models import Cronometro, Painel
from sapl.parlamentares.models import CargoMesa, Coligacao, ComposicaoColigacao, ComposicaoMesa, Dependente, Filiacao, Frente, Legislatura, Mandato, NivelInstrucao, Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar, TipoAfastamento, TipoDependente, Votante
from sapl.protocoloadm.models import AcompanhamentoDocumento, DocumentoAcessorioAdministrativo, DocumentoAdministrativo, Protocolo, StatusTramitacaoAdministrativo, TipoDocumentoAdministrativo, TramitacaoAdministrativo
from sapl.sessao.models import Bancada, CargoBancada, ExpedienteMateria, ExpedienteSessao, IntegranteMesa, OcorrenciaSessao, Orador, OradorExpediente, OrdemDia, PresencaOrdemDia, RegistroVotacao, ResumoOrdenacao, SessaoPlenaria, SessaoPlenariaPresenca, TipoExpediente, TipoResultadoVotacao, TipoSessaoPlenaria, VotoParlamentar

from cmj.s3_to_cmj.adjust import adjust_tipoafastamento, adjust_tipo_comissao,\
    adjust_statustramitacao, adjust_tipo_autor, adjust_tiporesultadovotacao,\
    adjust_orgao, adjust_assunto_norma, adjust_comissao, adjust_parlamentar,\
    adjust_mandato, adjust_autor, adjust_sessaoplenaria,\
    adjust_protocolo, adjust_documentoadministrativo,\
    adjust_documentoacessorioadministrativo, adjust_materialegislativa,\
    adjust_documentoacessorio, adjust_tramitacao, adjust_registrovotacao, \
    adjust_expediente_ordem, adjust_registrovotacao_parlamentar,\
    adjust_normajuridica, adjust_normarelacionada, adjust_participacao
from cmj.s3_to_cmj.models import (
    S3AcompMateria, S3Afastamento, S3Anexada, S3AssuntoNorma, S3Autor, S3Autoria,
    S3CargoComissao, S3CargoMesa, S3Comissao, S3ComposicaoComissao, S3ComposicaoMesa,
    S3CronometroAparte, S3CronometroDiscurso, S3CronometroOrdem, S3DespachoInicial,
    S3Dispositivo, S3DocumentoAcessorio, S3DocumentoAcessorioAdministrativo,
    S3DocumentoAdministrativo, S3ExpedienteMateria, S3ExpedienteSessaoPlenaria,
    S3Filiacao, S3LegislacaoCitada, S3Legislatura, S3Localidade, S3Mandato,
    S3MateriaLegislativa, S3MesaSessaoPlenaria, S3NormaJuridica, S3Numeracao,
    S3OradoresExpediente, S3OrdemDia, S3OrdemDiaPresenca, S3Orgao, S3Origem,
    S3Parlamentar, S3Partido, S3PeriodoCompComissao, S3PeriodoCompMesa, S3Proposicao,
    S3Protocolo, S3RegimeTramitacao, S3RegistroPresencaOrdem,
    S3RegistroPresencaSessao, S3RegistroVotacao, S3RegistroVotacaoParlamentar,
    S3Relatoria, S3ReuniaoComissao, S3SessaoLegislativa, S3SessaoPlenaria,
    S3SessaoPlenariaPresenca, S3StatusTramitacao, S3StatusTramitacaoAdministrativo,
    S3StatusTramitacaoParecer, S3TipoAfastamento, S3TipoAutor, S3TipoComissao,
    S3TipoDependente, S3TipoDocumento, S3TipoDocumentoAdministrativo,
    S3TipoExpediente, S3TipoFimRelatoria, S3TipoMateriaLegislativa,
    S3TipoNormaJuridica, S3TipoParecer, S3TipoProposicao, S3TipoResultadoVotacao,
    S3TipoSessaoPlenaria, S3TipoSituacaoMateria, S3TipoSituacaoMilitar,
    S3TipoSituacaoNorma, S3Tramitacao, S3TramitacaoAdministrativo,
    S3TramitacaoParecer, S3UnidadeTramitacao, S3VinculoNormaJuridica)


mapa = [
    {
        'name': 'nao importar',
        's31_model': [
            AudienciaPublica,
            TipoAudienciaPublica,
            CasaLegislativa,
            AppConfig,
            NivelInstrucao,
            Frente,
            AssuntoMateria,
            MateriaAssunto,
            TipoVinculoNormaJuridica,
            CargoBancada,
            ResumoOrdenacao,
            LexmlProvedor,
            LexmlPublicador,
            Painel,
            Cronometro,
            TipoNota,
            TipoVide,
            TipoDispositivo,
            TipoPublicacao,
            VeiculoPublicacao,
            Vide,
            Nota,
            Dispositivo,
            Publicacao,
            TipoDispositivoRelationship,
            TextoArticulado,
            TipoTextoArticulado,
            PerfilEstruturalTextoArticulado,
            AcompanhamentoDocumento,
            Bancada,
            Coligacao,
            AnexoAudienciaPublica,
            AcompanhamentoMateria,
            ComposicaoColigacao,
            AnexoNormaJuridica,
            OcorrenciaSessao,
            ComissoesDocumentoAcessorio,
            TipoProposicao,
            Dependente,
            Votante,
            Composicao,
            Reuniao,
            Proposicao,
            Orador,
            OradorExpediente,
            Numeracao,
            Relatoria,
            Parecer,
            DespachoInicial,
            AutoriaNorma,
            'NormaJuridica_assuntos',


            'TipoProposicao_perfis',
            'Frente_parlamentares',
            'Bloco_partidos',

        ]
    },
    {
        'name': '_legislatura',
        's30_model': S3Legislatura,
        's31_model': Legislatura,
        'fields': {
            'id': 'num_legislatura',
            'numero': 'num_legislatura',
            'data_inicio': 'dat_inicio',
            'data_fim': 'dat_fim',
            'data_eleicao': 'dat_eleicao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_partido',
        's30_model': S3Partido,
        's31_model': Partido,
        'fields': {
            'id': 'cod_partido',
            'sigla': 'sgl_partido',
            'nome': 'nom_partido',
            'data_criacao': 'dat_criacao',
            'data_extincao': 'dat_extincao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipodependente',
        's30_model': S3TipoDependente,
        's31_model': TipoDependente,
        'fields': {
            'id': 'tip_dependente',
            'descricao': 'des_tipo_dependente',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipoafastamento',
        's30_model': S3TipoAfastamento,
        's31_model': TipoAfastamento,
        'fields': {
            'id': 'tip_afastamento',
            'descricao': 'des_afastamento',
            'dispositivo': 'des_dispositivo',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_tipoafastamento,
    },
    {
        'name': '_cargomesa',
        's30_model': S3CargoMesa,
        's31_model': CargoMesa,
        'fields': {
            'id': 'cod_cargo',
            'descricao': 'des_cargo',
            'unico': 'ind_unico',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipocomissao',
        's30_model': S3TipoComissao,
        's31_model': TipoComissao,
        'fields': {
            'id': 'tip_comissao',
            'nome': 'nom_tipo_comissao',
            'natureza': 'sgl_natureza_comissao',
            'sigla': 'sgl_tipo_comissao',
            'dispositivo_regimental': 'des_dispositivo_regimental',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_tipo_comissao
    },

    {
        'name': '_periodocompcomissao',
        's30_model': S3PeriodoCompComissao,
        's31_model': Periodo,
        'fields': {
            'id': 'cod_periodo_comp',
            'data_inicio': 'dat_inicio_periodo',
            'data_fim': 'dat_fim_periodo',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_cargocomissao',
        's30_model': S3CargoComissao,
        's31_model': CargoComissao,
        'fields': {
            'id': 'cod_cargo',
            'nome': 'des_cargo',
            'unico': 'ind_unico',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipomaterialegislativa',
        's30_model': S3TipoMateriaLegislativa,
        's31_model': TipoMateriaLegislativa,
        'fields': {
            'id': 'tip_materia',
            'sigla': 'sgl_tipo_materia',
            'descricao': 'des_tipo_materia',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_statustramitacao',
        's30_model': S3StatusTramitacao,
        's31_model': StatusTramitacao,
        'fields': {
            'id': 'cod_status',
            'sigla': 'sgl_status',
            'descricao': 'des_status',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_statustramitacao
    },
    {
        'name': '_statustramitacaoadministrativo',
        's30_model': S3StatusTramitacaoAdministrativo,
        's31_model': StatusTramitacaoAdministrativo,
        'fields': {
            'id': 'cod_status',
            'sigla': 'sgl_status',
            'descricao': 'des_status',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_statustramitacao
    },

    {
        'name': '_tipoautor',
        's30_model': S3TipoAutor,
        's31_model': TipoAutor,
        'fields': {
            'id': 'tip_autor',
            'descricao': 'des_tipo_autor',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_tipo_autor
    },
    {
        'name': '_tipodocumento',
        's30_model': S3TipoDocumento,
        's31_model': TipoDocumento,
        'fields': {
            'id': 'tip_documento',
            'descricao': 'des_tipo_documento',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipodocumentoadministrativo',
        's30_model': S3TipoDocumentoAdministrativo,
        's31_model': TipoDocumentoAdministrativo,
        'fields': {
            'id': 'tip_documento',
            'sigla': 'sgl_tipo_documento',
            'descricao': 'des_tipo_documento',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipoexpediente',
        's30_model': S3TipoExpediente,
        's31_model': TipoExpediente,
        'fields': {
            'id': 'cod_expediente',
            'nome': 'nom_expediente',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tipofimrelatoria',
        's30_model': S3TipoFimRelatoria,
        's31_model': TipoFimRelatoria,
        'fields': {
            'id': 'tip_fim_relatoria',
            'descricao': 'des_fim_relatoria',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tiponormajuridica',
        's30_model': S3TipoNormaJuridica,
        's31_model': TipoNormaJuridica,
        'fields': {
            'id': 'tip_norma',
            'sigla': 'sgl_tipo_norma',
            'descricao': 'des_tipo_norma',
            'equivalente_lexml': 'voc_lexml',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tiporesultadovotacao',
        's30_model': S3TipoResultadoVotacao,
        's31_model': TipoResultadoVotacao,
        'fields': {
            'id': 'tip_resultado_votacao',
            'nome': 'nom_resultado',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_tiporesultadovotacao
    },
    {
        'name': '_tiposessaoplenaria',
        's30_model': S3TipoSessaoPlenaria,
        's31_model': TipoSessaoPlenaria,
        'fields': {
            'id': 'tip_sessao',
            'nome': 'nom_sessao',
            'quorum_minimo': 'num_minimo',
            'ind_excluido': 'ind_excluido',
        }
    },
    {
        'name': '_assuntonorma',
        's30_model': S3AssuntoNorma,
        's31_model': AssuntoNorma,
        'fields': {
            'id': 'cod_assunto',
            'assunto': 'des_assunto',
            'descricao': 'des_estendida',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_assunto_norma
    },
    {
        'name': '_orgao',
        's30_model': S3Orgao,
        's31_model': Orgao,
        'fields': {
            'id': 'cod_orgao',
            'nome': 'nom_orgao',
            'sigla': 'sgl_orgao',
            'unidade_deliberativa': 'ind_unid_deliberativa',
            'endereco': 'end_orgao',
            'telefone': 'num_tel_orgao',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_orgao
    },
    {
        'name': '_origem',
        's30_model': S3Origem,
        's31_model': Origem,
        'fields': {
            'id': 'cod_origem',
            'sigla': 'sgl_origem',
            'nome': 'nom_origem',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_regimetramitacao',
        's30_model': S3RegimeTramitacao,
        's31_model': RegimeTramitacao,
        'fields': {
            'id': 'cod_regime_tramitacao',
            'descricao': 'des_regime_tramitacao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_tiposituacaomilitar',
        's30_model': S3TipoSituacaoMilitar,
        's31_model': SituacaoMilitar,
        'fields': {
            'id': 'tip_situacao_militar',
            'descricao': 'des_tipo_situacao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_comissao',
        's30_model': S3Comissao,
        's31_model': Comissao,
        'fields': {
            'id': 'cod_comissao',
            'tipo_id': 'tip_comissao',
            'nome': 'nom_comissao',
            'sigla': 'sgl_comissao',
            'data_criacao': 'dat_criacao',
            'data_extincao': 'dat_extincao',
            'apelido_temp': 'nom_apelido_temp',
            'data_instalacao_temp': 'dat_instalacao_temp',
            'data_final_prevista_temp': 'dat_final_prevista_temp',
            'data_prorrogada_temp': 'dat_prorrogada_temp',
            'data_fim_comissao': 'dat_fim_comissao',
            'secretario': 'nom_secretario',
            'telefone_reuniao': 'num_tel_reuniao',
            'endereco_secretaria': 'end_secretaria',
            'telefone_secretaria': 'num_tel_secretaria',
            'fax_secretaria': 'num_fax_secretaria',
            'agenda_reuniao': 'des_agenda_reuniao',
            'local_reuniao': 'loc_reuniao',
            'finalidade': 'txt_finalidade',
            'email': 'end_email',
            'unidade_deliberativa': 'ind_unid_deliberativa',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_comissao
    },
    {
        'name': '_sessaolegislativa',
        's30_model': S3SessaoLegislativa,
        's31_model': SessaoLegislativa,
        'fields': {
            'id': 'cod_sessao_leg',
            'legislatura_id': 'num_legislatura',
            'numero': 'num_sessao_leg',
            'tipo': 'tip_sessao_leg',
            'data_inicio': 'dat_inicio',
            'data_fim': 'dat_fim',
            'data_inicio_intervalo': 'dat_inicio_intervalo',
            'data_fim_intervalo': 'dat_fim_intervalo',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_parlamentar',
        's30_model': S3Parlamentar,
        's31_model': Parlamentar,
        'fields': {
            'id': 'cod_parlamentar',
            'nivel_instrucao_id': 'cod_nivel_instrucao',
            'situacao_militar_id': 'tip_situacao_militar',
            'nome_completo': 'nom_completo',
            'nome_parlamentar': 'nom_parlamentar',
            'sexo': 'sex_parlamentar',
            'data_nascimento': 'dat_nascimento',
            'cpf': 'num_cpf',
            'rg': 'num_rg',
            'titulo_eleitor': 'num_tit_eleitor',
            'numero_gab_parlamentar': 'num_gab_parlamentar',
            'telefone': 'num_tel_parlamentar',
            'fax': 'num_fax_parlamentar',
            'endereco_residencia': 'end_residencial',
            'cep_residencia': 'num_cep_resid',
            'telefone_residencia': 'num_tel_resid',
            'fax_residencia': 'num_fax_resid',
            'endereco_web': 'end_web',
            'profissao': 'nom_profissao',
            'email': 'end_email',
            'locais_atuacao': 'des_local_atuacao',
            'ativo': 'ind_ativo',
            'biografia': 'txt_biografia',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_parlamentar
    },
    {
        'name': '_filiacao',
        's30_model': S3Filiacao,
        's31_model': Filiacao,
        'fields': {
            'id': 'cod_filiacao',
            'data': 'dat_filiacao',
            'parlamentar_id': 'cod_parlamentar',
            'partido_id': 'cod_partido',
            'data_desfiliacao': 'dat_desfiliacao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_composicaomesa',
        's30_model': S3ComposicaoMesa,
        's31_model': ComposicaoMesa,
        'fields': {
            'id': 'cod_composicao',
            'parlamentar_id': 'cod_parlamentar',
            'sessao_legislativa_id': 'cod_sessao_leg',
            'cargo_id': 'cod_cargo',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_mandato',
        's30_model': S3Mandato,
        's31_model': Mandato,
        'fields': {
            'id': 'cod_mandato',
            'parlamentar_id': 'cod_parlamentar',
            'tipo_afastamento_id': 'tip_afastamento',
            'legislatura_id': 'num_legislatura',
            'coligacao_id': 'cod_coligacao',
            'data_inicio_mandato': 'dat_inicio_mandato',
            'tipo_causa_fim_mandato': 'tip_causa_fim_mandato',
            'data_fim_mandato': 'dat_fim_mandato',
            'votos_recebidos': 'num_votos_recebidos',
            'data_expedicao_diploma': 'dat_expedicao_diploma',
            'observacao': 'txt_observacao',
            'titular': 'ind_titular',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_mandato
    },

    {
        'name': '_composicaocomissao',
        's30_model': S3ComposicaoComissao,
        's31_model': Participacao,
        'fields': {
            'id': 'cod_comp_comissao',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_participacao
    },

    {
        'name': '_autor',
        's30_model': S3Autor,
        's31_model': Autor,
        'fields': {
            'id': 'cod_autor',
            'nome': 'nom_autor',
            'cargo': 'des_cargo',
            'tipo_id': 'tip_autor',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_autor
    },
    {
        'name': '_unidadetramitacao',
        's30_model': S3UnidadeTramitacao,
        's31_model': UnidadeTramitacao,
        'fields': {
            'id': 'cod_unid_tramitacao',
            'comissao_id': 'cod_comissao',
            'orgao_id': 'cod_orgao',
            'parlamentar_id': 'cod_parlamentar',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_sessaoplenaria',
        's30_model': S3SessaoPlenaria,
        's31_model': SessaoPlenaria,
        'fields': {
            'id': 'cod_sessao_plen',
            'cod_andamento_sessao': 'cod_andamento_sessao',
            'tipo_id': 'tip_sessao',
            'sessao_legislativa_id': 'cod_sessao_leg',
            'legislatura_id': 'num_legislatura',
            'data_inicio': 'dat_inicio_sessao',
            'hora_inicio': 'hr_inicio_sessao',
            'hora_fim': 'hr_fim_sessao',
            'numero': 'num_sessao_plen',
            'data_fim': 'dat_fim_sessao',
            'url_audio': 'url_audio',
            'url_video': 'url_video',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_sessaoplenaria,
    },
    {
        'name': '_expedientesessaoplenaria',
        's30_model': S3ExpedienteSessaoPlenaria,
        's31_model': ExpedienteSessao,
        'fields': {
            'id': 'cod_exp',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'tipo_id': 'cod_expediente',
            'conteudo': 'txt_expediente',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_mesasessaoplenaria',
        's30_model': S3MesaSessaoPlenaria,
        's31_model': IntegranteMesa,
        'fields': {
            'id': 'cod_integrante',
            'cargo_id': 'cod_cargo',
            'parlamentar_id': 'cod_parlamentar',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_sessaoplenariapresenca',
        's30_model': S3SessaoPlenariaPresenca,
        's31_model': SessaoPlenariaPresenca,
        'fields': {
            'id': 'cod_presenca',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'parlamentar_id': 'cod_parlamentar',
            'ind_excluido': 'ind_excluido',
            'data_sessao': 'dat_presenca',
        }
    },
    {
        'name': '_ordemdiapresenca',
        's30_model': S3OrdemDiaPresenca,
        's31_model': PresencaOrdemDia,
        'fields': {
            'id': 'cod_presenca_ordem_dia',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'parlamentar_id': 'cod_parlamentar',
            'ind_excluido': 'ind_excluido',
        }
    },
    {
        'name': '_protocolo',
        's30_model': S3Protocolo,
        's31_model': Protocolo,
        'fields': {
            'id': 'cod_protocolo',
            'numero': 'num_protocolo',
            'ano': 'ano_protocolo',
            'data': 'dat_protocolo',
            'hora': 'hor_protocolo',
            'timestamp': 'dat_timestamp',
            'tipo_protocolo': 'tip_protocolo',
            'tipo_processo': 'tip_processo',
            'interessado': 'txt_interessado',
            'autor_id': 'cod_autor',
            'assunto_ementa': 'txt_assunto_ementa',
            'tipo_documento_id': 'tip_documento',
            'tipo_materia_id': 'tip_materia',
            'numero_paginas': 'num_paginas',
            'observacao': 'txt_observacao',
            'anulado': 'ind_anulado',
            'user_anulacao': 'txt_user_anulacao',
            'ip_anulacao': 'txt_ip_anulacao',
            'justificativa_anulacao': 'txt_just_anulacao',
            'timestamp_anulacao': 'timestamp_anulacao',
        },
        'adjust': adjust_protocolo
    },
    {
        'name': '_documentoadministrativo',
        's30_model': S3DocumentoAdministrativo,
        's31_model': DocumentoAdministrativo,
        'fields': {
            'id': 'cod_documento',
            'tipo_id': 'tip_documento',
            'numero': 'num_documento',
            'ano': 'ano_documento',
            'data': 'dat_documento',
            'interessado': 'txt_interessado',
            'autor_id': 'cod_autor',
            'dias_prazo': 'num_dias_prazo',
            'data_fim_prazo': 'dat_fim_prazo',
            'tramitacao': 'ind_tramitacao',
            'assunto': 'txt_assunto',
            'observacao': 'txt_observacao',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_documentoadministrativo
    },
    {
        'name': '_documentoacessorioadministrativo',
        's30_model': S3DocumentoAcessorioAdministrativo,
        's31_model': DocumentoAcessorioAdministrativo,
        'fields': {
            'id': 'cod_documento_acessorio',
            'documento_id': 'cod_documento',
            'tipo_id': 'tip_documento',
            'nome': 'nom_documento',
            'data': 'dat_documento',
            'autor': 'nom_autor_documento',
            'assunto': 'txt_assunto',
            'indexacao': 'txt_indexacao',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_documentoacessorioadministrativo
    },
    {
        'name': '_tramitacaoadministrativo',
        's30_model': S3TramitacaoAdministrativo,
        's31_model': TramitacaoAdministrativo,
        'fields': {
            'id': 'cod_tramitacao',
            'documento_id': 'cod_documento',
            'data_tramitacao': 'dat_tramitacao',
            'unidade_tramitacao_local_id': 'cod_unid_tram_local',
            'data_encaminhamento': 'dat_encaminha',
            'unidade_tramitacao_destino_id': 'cod_unid_tram_dest',
            'status_id': 'cod_status',
            'texto': 'txt_tramitacao',
            'data_fim_prazo': 'dat_fim_prazo',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_materialegislativa',
        's30_model': S3MateriaLegislativa,
        's31_model': MateriaLegislativa,
        'fields': {
            'id': 'cod_materia',
            'tipo_id': 'tip_id_basica',
            'numero_protocolo': 'num_protocolo',
            'numero': 'num_ident_basica',
            'ano': 'ano_ident_basica',
            'data_apresentacao': 'dat_apresentacao',
            'regime_tramitacao_id': 'cod_regime_tramitacao',
            'data_publicacao': 'dat_publicacao',
            'tipo_origem_externa_id': 'tip_origem_externa',
            'numero_origem_externa': 'num_origem_externa',
            'ano_origem_externa': 'ano_origem_externa',
            'data_origem_externa': 'dat_origem_externa',
            'local_origem_externa_id': 'cod_local_origem_externa',
            'apelido': 'nom_apelido',
            'dias_prazo': 'num_dias_prazo',
            'data_fim_prazo': 'dat_fim_prazo',
            'em_tramitacao': 'ind_tramitacao',
            'polemica': 'ind_polemica',
            'objeto': 'des_objeto',
            'complementar': 'ind_complementar',
            'ementa': 'txt_ementa',
            'indexacao': 'txt_indexacao',
            'observacao': 'txt_observacao',
            'resultado': 'txt_resultado',
            'ind_excluido': 'ind_excluido',
        },
        'adjust': adjust_materialegislativa
    },
    {
        'name': '_anexada',
        's30_model': S3Anexada,
        's31_model': Anexada,
        'fields': {
            'id': 'cod_anexada',
            'materia_principal_id': 'cod_materia_principal',
            'materia_anexada_id': 'cod_materia_anexada',
            'data_anexacao': 'dat_anexacao',
            'data_desanexacao': 'dat_desanexacao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_autoria',
        's30_model': S3Autoria,
        's31_model': Autoria,
        'fields': {
            'id': 'cod_autoria',
            'autor_id': 'cod_autor',
            'materia_id': 'cod_materia',
            'primeiro_autor': 'ind_primeiro_autor',
            'ind_excluido': 'ind_excluido'
        }
    },

    {
        'name': '_documentoacessorio',
        's30_model': S3DocumentoAcessorio,
        's31_model': DocumentoAcessorio,
        'fields': {
            'id': 'cod_documento',
            'materia_id': 'cod_materia',
            'tipo_id': 'tip_documento',
            'nome': 'nom_documento',
            'data': 'dat_documento',
            'autor': 'nom_autor_documento',
            'ementa': 'txt_ementa',
            'indexacao': 'txt_observacao',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_documentoacessorio
    },
    {
        'name': '_tramitacao',
        's30_model': S3Tramitacao,
        's31_model': Tramitacao,
        'fields': {
            'id': 'cod_tramitacao',
            'status_id': 'cod_status',
            'materia_id': 'cod_materia',
            'data_tramitacao': 'dat_tramitacao',
            'unidade_tramitacao_local_id': 'cod_unid_tram_local',
            'data_encaminhamento': 'dat_encaminha',
            'unidade_tramitacao_destino_id': 'cod_unid_tram_dest',
            'urgente': 'ind_urgencia',
            'turno': 'sgl_turno',
            'texto': 'txt_tramitacao',
            'data_fim_prazo': 'dat_fim_prazo',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_tramitacao
    },
    {
        'name': '_expedientemateria',
        's30_model': S3ExpedienteMateria,
        's31_model': ExpedienteMateria,
        'fields': {
            'id': 'cod_ordem',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'materia_id': 'cod_materia',
            'data_ordem': 'dat_ordem',
            'observacao': 'txt_tramitacao',
            'ind_excluido': 'ind_excluido',
            'numero_ordem': 'num_ordem',
            'tipo_votacao': 'tip_votacao',
        },
        'adjust': adjust_expediente_ordem
    },
    {
        'name': '_ordemdia',
        's30_model': S3OrdemDia,
        's31_model': OrdemDia,
        'fields': {
            'id': 'cod_ordem',
            'sessao_plenaria_id': 'cod_sessao_plen',
            'materia_id': 'cod_materia',
            'data_ordem': 'dat_ordem',
            'observacao': 'txt_tramitacao',
            'ind_excluido': 'ind_excluido',
            'numero_ordem': 'num_ordem',
            'tipo_votacao': 'tip_votacao',
        },
        'adjust': adjust_expediente_ordem
    },
    {
        'name': '_registrovotacao',
        's30_model': S3RegistroVotacao,
        's31_model': RegistroVotacao,
        'fields': {
            'id': 'cod_votacao',
            'tipo_resultado_votacao_id': 'tip_resultado_votacao',
            'materia_id': 'cod_materia',
            'numero_votos_sim': 'num_votos_sim',
            'numero_votos_nao': 'num_votos_nao',
            'numero_abstencoes': 'num_abstencao',
            'observacao': 'txt_observacao',
            'ind_excluido': 'ind_excluido',
        },
        'adjust': adjust_registrovotacao
    },

    {
        'name': '_registrovotacaoparlamentar',
        's30_model': S3RegistroVotacaoParlamentar,
        's31_model': VotoParlamentar,
        'fields': {
            'id': 'cod_vot_parlamentar',
            'votacao_id': 'cod_votacao',
            'parlamentar_id': 'cod_parlamentar',
            'ind_excluido': 'ind_excluido',
            'voto': 'vot_parlamentar',
        },
        'adjust': adjust_registrovotacao_parlamentar
    },

    {
        'name': '_normajuridica',
        's30_model': S3NormaJuridica,
        's31_model': NormaJuridica,
        'fields': {
            'id': 'cod_norma',
            'tipo_id': 'tip_norma',
            'materia_id': 'cod_materia',
            'numero': 'num_norma',
            'ano': 'ano_norma',
            'esfera_federacao': 'tip_esfera_federacao',
            'data': 'dat_norma',
            'data_publicacao': 'dat_publicacao',
            'veiculo_publicacao': 'des_veiculo_publicacao',
            'pagina_inicio_publicacao': 'num_pag_inicio_publ',
            'pagina_fim_publicacao': 'num_pag_fim_publ',
            'ementa': 'txt_ementa',
            'indexacao': 'txt_indexacao',
            'observacao': 'txt_observacao',
            'complemento': 'ind_complemento',
            'ind_excluido': 'ind_excluido',
            'data_vigencia': 'dat_vigencia',
            'timestamp': 'timestamp'
        },
        'adjust': adjust_normajuridica
    },
    {
        'name': '_legislacaocitada',
        's30_model': S3LegislacaoCitada,
        's31_model': LegislacaoCitada,
        'fields': {
            'id': 'cod_legis_citada',
            'materia_id': 'cod_materia',
            'norma_id': 'cod_norma',
            #'disposicoes': 'des_disposicoes',
            #'parte': 'des_parte',
            #'livro': 'des_livro',
            #'titulo': 'des_titulo',
            #'capitulo': 'des_capitulo',
            #'secao': 'des_secao',
            #'subsecao': 'des_subsecao',
            #'artigo': 'des_artigo',
            #'paragrafo': 'des_paragrafo',
            #'inciso': 'des_inciso',
            #'alinea': 'des_alinea',
            #'item': 'des_item',
            'ind_excluido': 'ind_excluido'
        }
    },

    {
        'name': '_vinculonormajuridica',
        's30_model': S3VinculoNormaJuridica,
        's31_model': NormaRelacionada,
        'fields': {
            'id': 'cod_vinculo',
            'norma_principal_id': 'cod_norma_referente',
            'norma_relacionada_id': 'cod_norma_referida',
            'ind_excluido': 'ind_excluido'
        },
        'adjust': adjust_normarelacionada
    },

    {
        'name': '_ocorrenciasessao',
        's30_model': None,
        's31_model': OcorrenciaSessao,  # para clear
        'fields': {}
    },
]

mapa_a_processar = [
    # TODO: processar




    {
        'name': '_afastamento',
        's30_model': S3Afastamento,
        's31_model': None,
        'fields': {
            '': 'cod_afastamento',
            '': 'cod_parlamentar',
            '': 'cod_mandato',
            '': 'num_legislatura',
            '': 'tip_afastamento',
            '': 'dat_inicio_afastamento',
            '': 'dat_fim_afastamento',
            '': 'cod_parlamentar_suplente',
            '': 'txt_observacao',
            'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_cronometroaparte',
        's30_model': S3CronometroAparte,
        's31_model': None,
        'fields': {
            '': 'id',
            '': 'int_reset',
                '': 'int_start',
                '': 'int_stop'
        }
    },
    {
        'name': '_cronometrodiscurso',
        's30_model': S3CronometroDiscurso,
        's31_model': None,
        'fields': {
            '': 'id',
            '': 'int_reset',
                '': 'int_start',
                '': 'int_stop'
        }
    },
    {
        'name': '_cronometroordem',
        's30_model': S3CronometroOrdem,
        's31_model': None,
        'fields': {
            '': 'id',
            '': 'int_reset',
                '': 'int_start',
                '': 'int_stop'
        }
    },
    {
        'name': '_despachoinicial',
        's30_model': S3DespachoInicial,
        's31_model': None,
        'fields': {
            '': 'id',
            '': 'cod_materia',
                '': 'num_ordem',
                '': 'cod_comissao',
                'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_dispositivo',
        's30_model': S3Dispositivo,
        's31_model': None,
        'fields': {
            '': 'cod_dispositivo',
            '': 'num_ordem',
                '': 'num_ordem_bloco_atualizador',
                '': 'num_nivel',
                '': 'num_dispositivo_0',
                '': 'num_dispositivo_1',
                '': 'num_dispositivo_2',
                '': 'num_dispositivo_3',
                '': 'num_dispositivo_4',
                '': 'num_dispositivo_5',
                '': 'txt_rotulo',
                '': 'txt_texto',
                '': 'txt_texto_atualizador',
                '': 'dat_inicio_vigencia',
                '': 'dat_fim_vigencia',
                '': 'dat_inicio_eficacia',
                '': 'dat_fim_eficacia',
                '': 'ind_visibilidade',
                '': 'ind_validade',
                '': 'tim_atualizacao_banco',
                '': 'cod_norma',
                '': 'cod_norma_publicada',
                '': 'cod_dispositivo_pai',
                '': 'cod_dispositivo_vigencia',
                '': 'cod_dispositivo_atualizador',
                '': 'cod_tipo_dispositivo',
                '': 'cod_publicacao'
        }
    },
    {
        'name': '_localidade',
        's30_model': S3Localidade,
        's31_model': None,
        'fields': {
            '': 'cod_localidade',
            '': 'nom_localidade',
                '': 'nom_localidade_pesq',
                '': 'tip_localidade',
                '': 'sgl_uf',
                '': 'sgl_regiao',
                'ind_excluido': 'ind_excluido'
        }
    },

    {
        'name': '_oradoresexpediente',
        's30_model': S3OradoresExpediente,
        's31_model': None,
        'fields': {
            '': 'id',
            '': 'cod_sessao_plen',
                '': 'cod_parlamentar',
                '': 'num_ordem',
                '': 'url_discurso',
                'ind_excluido': 'ind_excluido'
        }
    },

    {
        'name': '_periodocompmesa',
        's30_model': S3PeriodoCompMesa,
        's31_model': None,
        'fields': {
            '': 'cod_periodo_comp',
            '': 'num_legislatura',
                '': 'dat_inicio_periodo',
                '': 'dat_fim_periodo',
                'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_proposicao',
        's30_model': S3Proposicao,
        's31_model': None,
        'fields': {
            '': 'cod_proposicao',
            '': 'cod_materia',
                '': 'cod_autor',
                '': 'tip_proposicao',
                '': 'dat_envio',
                '': 'dat_recebimento',
                '': 'txt_descricao',
                '': 'cod_mat_ou_doc',
                '': 'dat_devolucao',
                '': 'txt_justif_devolucao',
                '': 'txt_observacao',
                'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_regimetramitacao',
        's30_model': S3RegimeTramitacao,
        's31_model': None,
        'fields': {
            '': 'cod_regime_tramitacao',
            '': 'des_regime_tramitacao',
                'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_registropresencaordem',
        's30_model': S3RegistroPresencaOrdem,
        's31_model': None,
        'fields': {
            '': 'cod_registro_pre',
            '': 'cod_sessao_plen',
                '': 'num_id_quorum',
                '': 'ind_status_pre',
                '': 'dat_abre_pre',
                '': 'dat_fecha_pre',
                'ind_excluido': 'ind_excluido'
        }
    },
    {
        'name': '_registropresencasessao',
        's30_model': S3RegistroPresencaSessao,
        's31_model': None,
        'fields': {
            '': 'cod_registro_pre',
            '': 'cod_sessao_plen',
            '': 'num_id_quorum',
            '': 'ind_status_pre',
            '': 'dat_abre_pre',
            '': 'dat_fecha_pre',
            'ind_excluido': 'ind_excluido'
        }
    },

]
