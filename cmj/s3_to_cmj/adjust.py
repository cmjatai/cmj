
from datetime import date, datetime
from operator import xor

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from sapl.comissoes.models import Participacao, Comissao, Composicao
from sapl.norma.models import AssuntoNorma, TipoVinculoNormaJuridica
from sapl.parlamentares.models import Legislatura, Parlamentar, Partido
from sapl.protocoloadm.models import Protocolo
from sapl.sessao.models import TipoResultadoVotacao, OrdemDia, ExpedienteMateria,\
    RegistroVotacao
from sapl.utils import normalize


def adjust_tipoafastamento(new, old):
    assert xor(old.ind_afastamento, old.ind_fim_mandato)
    if old.ind_afastamento:
        new.indicador = 'A'
    elif old.ind_fim_mandato:
        new.indicador = 'F'

    if old.des_dispositivo is None:
        new.dispositivo = ''


def adjust_tipo_comissao(new, old):
    if old.des_dispositivo_regimental is None:
        new.dispositivo_regimental = ''


def adjust_statustramitacao(new, old):
    if old.ind_fim_tramitacao:
        new.indicador = 'F'
    elif old.ind_retorno_tramitacao:
        new.indicador = 'R'
    else:
        new.indicador = ''


def adjust_tipo_autor(new, old):
    model_apontado = normalize(new.descricao.lower()).replace(' ', '')
    content_types = ContentType.objects.filter(model=model_apontado)
    assert len(content_types) <= 1
    new.content_type = content_types[0] if content_types else None


def adjust_tiporesultadovotacao(new, old):
    if 'aprova' in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.aprovado
    elif 'rejeita' in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.rejeitado
    elif 'retirado' in new.nome.lower():
        new.natureza = TipoResultadoVotacao.NATUREZA_CHOICES.rejeitado
    else:
        new.natureza = ''


def adjust_orgao(new, old):
    if not new.endereco:
        new.endereco = ''
    if not new.telefone:
        new.telefone = ''


def adjust_assunto_norma(new, old):
    if not new.descricao:
        new.descricao = ''


def adjust_comissao(new, old):
    if not old.dat_extincao and not old.dat_fim_comissao:
        new.ativa = True
    elif (old.dat_extincao and date.today() < new.data_extincao or
          old.dat_fim_comissao and date.today() < new.data_fim_comissao):
        new.ativa = True
    else:
        new.ativa = False


def adjust_parlamentar(new, old):
    new.municipio_residencia = 'Jataí'
    new.uf_residencia = 'GO'

    if not new.nivel_instrucao_id:
        new.nivel_instrucao = None

    if not new.situacao_militar_id:
        new.situacao_militar = None


def adjust_mandato(new, old):
    if old.dat_fim_mandato:
        new.data_fim_mandato = old.dat_fim_mandato
    if not new.data_fim_mandato:
        legislatura = Legislatura.objects.latest('data_fim')
        new.data_fim_mandato = legislatura.data_fim
        new.data_expedicao_diploma = legislatura.data_inicio
    if not new.data_inicio_mandato:
        new.data_inicio_mandato = new.legislatura.data_inicio
        new.data_fim_mandato = new.legislatura.data_fim

    if new.tipo_afastamento_id == 0:
        new.tipo_afastamento_id = None


def adjust_participacao(new, old):
    comp = Composicao.objects.filter(
        comissao_id=old.cod_comissao,
        periodo_id=old.cod_periodo_comp)
    if comp.exists():
        if comp.count() > 1:
            raise Exception("Existe mais de uma composição registrada")
        comp = comp.first()
    else:
        comp = Composicao()
        comp.comissao_id = old.cod_comissao
        comp.periodo_id = old.cod_periodo_comp
        comp.save()
    new.composicao_id = comp.id
    new.parlamentar_id = old.cod_parlamentar
    new.cargo_id = old.cod_cargo
    new.titular = old.ind_titular
    new.data_designacao = old.dat_designacao
    new.data_desligamento = old.dat_desligamento
    new.motivo_desligamento = old.des_motivo_desligamento
    new.observacao = old.obs_composicao


def adjust_autor(new, old):

    if old.cod_parlamentar:
        new.nome = Parlamentar.objects.get(
            pk=old.cod_parlamentar).nome_parlamentar
        new.object_id = old.cod_parlamentar
        new.content_type = ContentType.objects.get_for_model(Parlamentar)

    if old.cod_comissao:
        new.nome = Comissao.objects.get(pk=old.cod_comissao).nome
        new.object_id = old.cod_comissao
        new.content_type = ContentType.objects.get_for_model(Comissao)

    if not new.cargo:
        new.cargo = ''


def adjust_sessaoplenaria(new, old):
    if old.ind_iniciada is None:
        new.iniciada = False
        new.finalizada = True
    elif old.ind_iniciada == 1:
        new.iniciada = True
        new.finalizada = False
    else:
        new.iniciada = False
        new.finalizada = False

    if new.url_audio is None:
        new.url_audio = ''
    if new.url_video is None:
        new.url_video = ''

    new.expedientesessao_set.all().delete()


def adjust_protocolo(new, old):
    if not new.interessado:
        new.interessado = ''

    if not new.user_anulacao:
        new.user_anulacao = ''
    if not new.ip_anulacao:
        new.ip_anulacao = ''
    if not new.justificativa_anulacao:
        new.justificativa_anulacao = ''

    # Uma fase que se criou um autor "todos parlamentares"
    if new.autor_id == 21:
        new.autor_id = None


def adjust_documentoadministrativo(new, old):
    if old.num_protocolo:
        numero, ano = old.num_protocolo, new.ano
        # False < True => o primeiro será o protocolo não anulado
        protocolos = Protocolo.objects.filter(
            numero=numero, ano=ano).order_by('anulado')
        if protocolos:
            new.protocolo = protocolos[0]
        else:
            # Se não achamos o protocolo registramos no número externo
            new.numero_externo = numero
    new.workspace_id = 20


def adjust_parecerprocuradoria(new, old):
    if old.num_protocolo:
        numero, ano = old.num_protocolo, new.ano
        # False < True => o primeiro será o protocolo não anulado
        protocolos = Protocolo.objects.filter(
            numero=numero, ano=ano).order_by('anulado')
        if protocolos:
            new.protocolo = protocolos[0]
        else:
            # Se não achamos o protocolo registramos no número externo
            new.numero_externo = numero
    new.workspace_id = 21


def adjust_tipo_documento_administrativo(new, old):
    new.workspace_id = 20


def adjust_tipo_parecer(new, old):
    new.workspace_id = 21


def adjust_documentoacessorioadministrativo(new, old):
    if not new.assunto:
        new.assunto = ''
    if not new.indexacao:
        new.indexacao = ''


def adjust_materialegislativa(new, old):
    new.tipo_apresentacao = 'E'

    if not new.resultado:
        new.resultado = ''


def adjust_documentoacessorio(new, old):
    if not new.ementa:
        new.ementa = ''
    if not new.indexacao:
        new.indexacao = ''


def adjust_tramitacao(new, old):
    new.timestamp = timezone.now()
    if not new.turno:
        new.turno = 'U'


def adjust_expediente_ordem(new, old):
    if not new.observacao:
        new.observacao = ''


def adjust_registrovotacao_parlamentar(new, old):

    votacao = RegistroVotacao.objects.get(pk=new.votacao_id)

    new.ordem = votacao.ordem
    new.expediente = votacao.expediente


def adjust_registrovotacao(new, old):

    if old.num_nao_votou:
        new.numero_abstencoes = new.numero_abstencoes + old.num_nao_votou

    ordem_dia = OrdemDia.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)
    expediente_materia = ExpedienteMateria.objects.filter(
        pk=old.cod_ordem, materia=old.cod_materia)

    if ordem_dia and not expediente_materia:
        new.ordem = ordem_dia[0]
    if not ordem_dia and expediente_materia:
        new.expediente = expediente_materia[0]

    # registro de votação ambíguo
    if ordem_dia and expediente_materia:
        raise Exception('Registro de Votação ambíguo')


def adjust_normajuridica(new, old):
    if not new.indexacao:
        new.indexacao = ''
    if not new.observacao:
        new.observacao = ''
    if not new.veiculo_publicacao:
        new.veiculo_publicacao = ''
    new.assuntos.clear()

    assuntos_id = old.cod_assunto.split(',')
    if not assuntos_id:
        return
    new.save()
    assuntos = AssuntoNorma.objects.filter(id__in=assuntos_id)
    if assuntos.exists():
        new.assuntos.add(*assuntos)


def adjust_normarelacionada(new, old):
    try:
        new.tipo_vinculo = TipoVinculoNormaJuridica.objects.get(
            sigla=old.tip_vinculo)
    except:
        tipo = TipoVinculoNormaJuridica()
        tipo.sigla = 'Z'
        tipo.descricao_ativa = 'Autógrafo da Norma:'
        tipo.descricao_passiva = 'Autógrafo Transformado em Lei'
        tipo.save()
        new.tipo_vinculo = tipo
