
from datetime import timedelta
import datetime
import mimetypes
from time import sleep

import dateutil
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.forms.models import model_to_dict
from django.utils import timezone
import urllib3

from cmj.core.models import AreaTrabalho, CertidaoPublicacao
from cmj.globalrules import GROUP_MATERIA_WORKSPACE_VIEWER
from cmj.legacy_sislegis_publicacoes.models import Tipodoc, Tipolei, Documento,\
    Assuntos
from sapl.compilacao.models import TextoArticulado, Dispositivo
from sapl.norma.models import NormaRelacionada
from sapl.protocoloadm.models import TipoDocumentoAdministrativo,\
    DocumentoAdministrativo, Anexado, TramitacaoAdministrativo,\
    StatusTramitacaoAdministrativo
from sapl.utils import RANGE_MESES


# MIGRAÇÃO DE DOCUMENTOS  ###################################################
EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/xml': '.xml',
    'text/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
    'image/gif': '.gif',
    'text/rtf': '.rtf',
    'text/x-python': '.py',
    'text/plain': '.ksh',
    'text/plain': '.c',
    'text/plain': '.h',
    'text/plain': '.txt',
    'text/plain': '.bat',
    'text/plain': '.pl',
    'text/plain': '.asc',
    'text/plain': '.text',
    'text/plain': '.pot',
    'text/plain': '.brf',
    'text/plain': '.srt',
    'image/tiff': '.tiff',
    'application/vnd.ms-excel': '.xlsx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
}


def get_extensao(mime):
    try:
        return EXTENSOES[mime]
    except KeyError as e:
        raise Exception('\n'.join([
            'mimetype:',
            mime,
            ' Algumas possibilidades são:', ] +
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)] +
            ['Atualize o código do dicionário EXTENSOES!']
        )) from e


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def reset_id_model(self, model):

        query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                    coalesce(max("id"), 1), max("id") IS NOT null) 
                    FROM "%(app_model_name)s";
                """ % {
            'app_model_name': _get_registration_key(model)
        }

        with connection.cursor() as cursor:
            cursor.execute(query)
            # get all the rows as a list
            rows = cursor.fetchall()
            print(rows)

    def handle(self, *args, **options):

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run__add_operadores_no_grupo_para_ver_pareceres()

        # self.reset_id_model(CertidaoPublicacao)
        # self.reset_id_model(TipoDocumentoAdministrativo)
        # self.reset_id_model(StatusTramitacaoAdministrativo)

    def run__add_operadores_no_grupo_para_ver_pareceres(self):
        ats = AreaTrabalho.objects.filter(ativo=True)

        g = Group.objects.get(name=GROUP_MATERIA_WORKSPACE_VIEWER)
        for at in ats:
            for o in at.operadorareatrabalho_set.all():
                o.user.groups.add(g)
                if not o.grupos_associados.filter(id=g.id).exists():
                    try:
                        o.grupos_associados.add(g)
                        o.user.groups.add(g)
                    except Exception as e:
                        print(e)
                    print(o.user, at)

    def run__remove_alteracoes_codigo_tributario(self):

        normas = NormaRelacionada.objects.filter(
            norma_relacionada_id=1117).order_by('-norma_principal__data')

        for n in normas:
            ta = n.norma_principal.texto_articulado.first()

            if ta:
                blocos = ta.dispositivos_set.filter(
                    tipo_dispositivo_id=3).order_by('-ordem')
                blocos.delete()
                print(ta)
                ta.editing_locked = False
                ta.privacidade = 89
                ta.save()

    def run__click_dispositivo_vigencia(self):
        # Dispositivo.objects.all().update(dispositivo_vigencia=None)
        tas = TextoArticulado.objects.all().order_by('data')

        count_sem_dvt = 0
        for ta in tas:
            dsss = ta.dispositivos_set.all()

            if not dsss:
                continue

            has_dvt = dsss.first().dispositivo_vigencia

            if has_dvt:
                continue

            dvt_encontrado = False
            for dvt_str in (
                'Esta Lei entrará em vigor na data da sua publicação',
                'Esta Lei entrará em vigor na data de sua publicação',
                'Esta Lei Ordinária entra em vigor na data de sua publicação',
                'Esta lei entra em vigor na data de sua publicação',
                'Este Decreto Legislativo entra em vigor na data de sua publicação',
                'Está Lei entrará em vigor na data de sua publicação',
                'Esta resolução entra em vigor na data de sua publicação',
                'Esta portaria entra em vigor na data de sua publicação',
                'A presente Lei entra em vigor na data de sua publicação',
                'A Presente Lei entrará em vigor na data de sua publicação'
                'Esta Lei entrará em vigor, na data de sua publicação',
                'Esta Lei entra em vigor a partir de sua publicação',
                'Esta Resolução entrará em vigor na data de sua publicação',
                'Este Decreto Legislativo entra em vigor a partir da data de sua publicação',
                'Este decreto legislativo entra em vigor na da data de sua publicação',
                'Este decreto legislativo entra em vigor na da data da sua publicação',
                'Esta Resolução entra avigor na data de sua publicação',
                'Este DECRETO - LEGISLATIVO entra em vigor na data de sua publicação',
                'Esta Lei n° 4.016/2018 entrará em vigor na data de sua publicação',
                'Esta Portaria entras em vigor na data de sua publicação',
                'Esta Lei entrará em na data de sua publicação',
                'Esta lei entra em vigor na data da sua publicação',
                'Esta emenda entra em vigor após a sua publicação',

            ):

                dvt = dsss.filter(texto__icontains=dvt_str).last()

                if dvt:
                    if dvt.dispositivo_vigencia:
                        dvt_encontrado = True
                        break

                    if dvt.auto_inserido:
                        dvt = dvt.dispositivo_pai
                    try:
                        Dispositivo.objects.filter(
                            ta=dvt.ta, ta_publicado__isnull=True
                        ).update(
                            dispositivo_vigencia=dvt,
                            inicio_vigencia=dvt.inicio_vigencia,
                            inicio_eficacia=dvt.inicio_eficacia)

                        Dispositivo.objects.filter(ta_publicado=dvt.ta
                                                   ).update(
                            dispositivo_vigencia=dvt,
                            inicio_vigencia=dvt.inicio_eficacia,
                            inicio_eficacia=dvt.inicio_eficacia)

                        dps = Dispositivo.objects.filter(
                            dispositivo_vigencia=dvt)
                        for d in dps:
                            if d.dispositivo_substituido:
                                ds = d.dispositivo_substituido
                                ds.fim_vigencia = d.inicio_vigencia - \
                                    timedelta(days=1)
                                ds.fim_eficacia = d.inicio_eficacia - \
                                    timedelta(days=1)
                                ds.save()

                            if d.dispositivo_subsequente:
                                ds = d.dispositivo_subsequente
                                d.fim_vigencia = ds.inicio_vigencia - \
                                    timedelta(days=1)
                                d.fim_eficacia = ds.inicio_eficacia - \
                                    timedelta(days=1)
                                d.save()
                    except Exception as e:
                        print("Ocorreu um erro ({}) na atualização do "
                              "Dispositivo de Vigência".format(str(e)))
                    dvt_encontrado = True
                    break

            if not dvt_encontrado:
                count_sem_dvt += 1
                print('dvt nao encontrado', ta.id, ta)
        print('T.A. sem dvt', count_sem_dvt)

    def run__check_automatico_normas_sem_bloco_e_sem_alteracao(self):
        tas = TextoArticulado.objects.all()

        for ta in tas:

            ds = ta.dispositivos_set.all()

            if not ds.filter(tipo_dispositivo_id=3).exists() and \
                    not ds.filter(ta_publicado_id__isnull=False).exists():
                ta.temp_check_migrations = True
                ta.save()
                print(ta.id, ta)

    def run__coloca_em_edicao_determinada_norma_e_suas_alteracoes(self):
        normas = NormaRelacionada.objects.filter(norma_relacionada_id=1117)

        for n in normas:
            ta = n.norma_principal.texto_articulado.first()

            if ta:
                print(ta)
                ta.editing_locked = False
                ta.privacidade = 89
                ta.save()

    def run__old4(self):
        tas = TextoArticulado.objects.all()

        for ta in tas:
            print(ta)
            ta.editable_only_by_owners = False
            ta.editing_locked = True
            ta.privacidade = 0
            ta.save()

    def run__corrige_datas_ultima_atualizacao_com_sislegis(self):

        at = AreaTrabalho.objects.get(pk=22)

        docs = DocumentoAdministrativo.objects.filter(
            workspace=at).order_by('id')

        for d in docs:
            j = d.old_json

            if j and 'data_alteracao' in j and j['data_alteracao']:
                d.data_ultima_atualizacao = datetime.datetime.strptime(
                    j['data_alteracao'], "%Y-%m-%dT%H:%M:%S").astimezone()
            d.save()

    def run__corrige_datas_ultima_atualizacao_na_propria_base(self):

        at = AreaTrabalho.objects.get(pk=21)

        docs = DocumentoAdministrativo.objects.filter(
            workspace=at).order_by('id')

        for d in docs:
            d.data_ultima_atualizacao = d.data
            d.save()

    def run__old2(self):
        at = AreaTrabalho.objects.get(pk=22)

        clear = False

        if clear:
            a = Anexado.objects.all()
            a.filter(documento_principal__workspace=at)
            a.delete()

        docs = DocumentoAdministrativo.objects.filter(
            workspace=at).order_by('id')

        print(docs.count())

        em_checar = 0

        StatusTramitacaoAdministrativo.objects.get_or_create(
            id=12, sigla='LICAND', indicador='R', workspace=at,
            descricao='Licitação em Andamento')

        StatusTramitacaoAdministrativo.objects.get_or_create(
            id=13, sigla='LICCASS', indicador='F', workspace=at,
            descricao='Licitação com Contrato Assinado')

        StatusTramitacaoAdministrativo.objects.get_or_create(
            id=14, sigla='LICENC', indicador='F', workspace=at,
            descricao='Licitação Encerrada')

        StatusTramitacaoAdministrativo.objects.get_or_create(
            id=15, sigla='LICCANC', indicador='F', workspace=at,
            descricao='Licitação Cancelada')

        StatusTramitacaoAdministrativo.objects.get_or_create(
            id=16, sigla='JUSTINEG', indicador='F', workspace=at,
            descricao='Justificativa de Inexigibilidade de Licitação')

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=189, sigla='TC', workspace=at,
            descricao='Termo de Credenciamento'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=190, sigla='CNTRT', workspace=at,
            descricao='Contrato'
        )
        TipoDocumentoAdministrativo.objects.get_or_create(
            id=191, sigla='EDCC', workspace=at,
            descricao='Edital Carta Convite'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=192, sigla='EDTP', workspace=at,
            descricao='Edital Tomada de Preços'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=193, sigla='EDPP', workspace=at,
            descricao='Edital Pregão Presencial'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=194, sigla='ATAP', workspace=at,
            descricao='Ato de Apostilamento'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=195, sigla='ADTCT', workspace=at,
            descricao='Aditivo de Contrato'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=196, sigla='EDCRD', workspace=at,
            descricao='Edital de Credenciamento'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=197, sigla='DPLIC', workspace=at,
            descricao='Dispensa de Licitação'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=198, sigla='PRTR', workspace=at,
            descricao='Portaria'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=200, sigla='ARPP', workspace=at,
            descricao='Ata de Realização de Pregão'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=201, sigla='CRDPR', workspace=at,
            descricao='Credenciamento de Pregão'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=202, sigla='ARP', workspace=at,
            descricao='Ata de Registro de Preços'
        )
        TipoDocumentoAdministrativo.objects.get_or_create(
            id=203, sigla='EDINT', workspace=at,
            descricao='Edital de Intimação'
        )
        TipoDocumentoAdministrativo.objects.get_or_create(
            id=204, sigla='IPIP', workspace=at,
            descricao='Instauração de Procedimento Investigatório Preliminar'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=205, sigla='PRPRG', workspace=at,
            descricao='Proposta de Pregão'
        )
        TipoDocumentoAdministrativo.objects.get_or_create(
            id=206, sigla='ATRN', workspace=at,
            descricao='Ata de Reunião'
        )
        TipoDocumentoAdministrativo.objects.get_or_create(
            id=207, sigla='TMHM', workspace=at,
            descricao='Termo de Homologação'
        )

        TipoDocumentoAdministrativo.objects.get_or_create(
            id=208, sigla='RGCP', workspace=at,
            descricao='Registro de Chapa'
        )

        qs_tipos = TipoDocumentoAdministrativo.objects.all()
        tipos = {}

        for tipo in qs_tipos:
            tipos[str(tipo.id)] = tipo

        user_adm = get_user_model().objects.get(id=1)

        for d in docs:
            j = d.old_json

            if not j:
                continue

            d.epigrafe = j['epigrafe']

            if not j['possuiarqdigital'] and d.texto_integral:
                d.texto_integral.delete()

            if clear and j['id_doc_principal']:
                a = Anexado()
                a.documento_principal_id = j['id_doc_principal']
                a.documento_anexado_id = d.id
                try:
                    a.data_anexacao = datetime.datetime.strptime(
                        j['data_inclusao'], "%Y-%m-%dT%H:%M:%S")
                except:
                    a.data_anexacao = d.data
                try:
                    a.save()
                except Exception as e:
                    print(e)
                    return

            """if j['cod_certidao'] > 0 and not d.certidao:
                cp = CertidaoPublicacao.gerar_certidao(
                    user_adm, d, 'texto_integral', d.id)

                if cp:
                    cp.created = datetime.datetime.strptime(
                        j['data_inclusao'], "%Y-%m-%dT%H:%M:%S")
                    cp.modified = datetime.datetime.strptime(
                        j['data_inclusao'], "%Y-%m-%dT%H:%M:%S")
                    cp.save()"""

            if 7 in j['tipos'] and len(j['tipos']) == 1:  # Balancetes Contábeis
                d.tipo = tipos['182']
                dbb = (d.data - timedelta(days=20)
                       ) if d.data.day < 15 else d.data
                d.numero = dbb.month
                d.year = dbb.year
                d.assunto = j['epigrafe']
                if not d.assunto:
                    print(dbb.month)
                    d.epigrafe = 'Balancete de %s de %s' % (
                        RANGE_MESES[d.numero - 1][1], dbb.year)
                    d.assunto = 'Balancete de %s de %s' % (
                        RANGE_MESES[d.numero - 1][1], dbb.year)

            # Balancetes Contábeis
            elif 25 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['183']
            elif 29 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['184']
            elif 8 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['185']
            elif 35 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['186']

            elif len(j['tipos']) == 1 and j['tipos'][0] in (38, 39, 40, 41) and not j['id_doc_principal']:
                d.tipo = tipos['187']
                d.tipo_id = 187
                d.tramitacao = True

                status = {
                    '38': 4,
                    '39': 5,
                    '40': 6,
                    '41': 7,
                }

                d.tramitacaoadministrativo_set.all().delete()
                for anexo in d.documento_principal_set.all().order_by('-id'):
                    t = TramitacaoAdministrativo()
                    t.status_id = status[str(j['tipos'][0])]
                    t.documento = d
                    if anexo.documento_anexado.certidao:
                        t.data_tramitacao = anexo.documento_anexado.certidao.created.date()
                    else:
                        t.data_tramitacao = anexo.documento_anexado.data
                    t.unidade_tramitacao_local_id = 3
                    t.unidade_tramitacao_destino_id = 3
                    t.texto = 'Publicação de: %s' % anexo.documento_anexado
                    t.save()

            elif len(j['tipos']) == 1 and j['tipos'][0] in (5, 31, 32, 33, 35) and not j['id_doc_principal']:
                d.tipo = tipos['187']
                d.tipo_id = 187
                d.tramitacao = True

                status = {
                    '5': 12,
                    '31': 13,
                    '32': 14,
                    '33': 15,
                    '35': 16,
                }

                d.tramitacaoadministrativo_set.all().delete()
                for anexo in d.documento_principal_set.all().order_by('-id'):
                    t = TramitacaoAdministrativo()
                    t.status_id = status[str(j['tipos'][0])]
                    t.documento = d
                    if anexo.documento_anexado.certidao:
                        t.data_tramitacao = anexo.documento_anexado.certidao.created.date()
                    else:
                        t.data_tramitacao = anexo.documento_anexado.data
                    t.unidade_tramitacao_local_id = 3
                    t.unidade_tramitacao_destino_id = 3
                    t.texto = 'Publicação de: %s' % anexo.documento_anexado
                    t.save()

            elif j['epigrafe'].startswith('Termo de Credenciamento'):
                d.tipo = tipos['189']
                d.tipo_id = 189

            elif j['epigrafe'].startswith('Contrato') or \
                    j['epigrafe'].startswith('Instrumento contratual'):
                d.tipo = tipos['190']
                d.tipo_id = 190

            elif j['id_doc_principal'] and (
                j['epigrafe'].startswith(' Carta Convite') or
                j['epigrafe'].startswith('Carta Convite') or
                j['epigrafe'].startswith('Carta  Convite') or
                j['epigrafe'].startswith('Edital Convite') or
                j['epigrafe'].startswith('Edital Carta') or
                j['epigrafe'].startswith('Edital  Carta') or
                j['epigrafe'].startswith('Edital  Convite') or
                j['epigrafe'].startswith(' Edital - Convite') or
                j['epigrafe'].startswith('Edital - Carta') or
                j['epigrafe'].startswith('Edital Carta Convite')
            ):
                d.tipo = tipos['191']
                d.tipo_id = 191

            elif j['id_doc_principal'] and (
                'Tomada de Preço'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['192']
                d.tipo_id = 192

            elif j['id_doc_principal'] and (
                'edital de pregão' in j['epigrafe'].lower() or
                'edital pregão' in j['epigrafe'].lower() or
                'edital  pregão' in j['epigrafe'].lower()

            ):
                d.tipo = tipos['193']
                d.tipo_id = 193

            elif j['id_doc_principal'] and (
                'ato de apostilamento' in j['epigrafe'].lower()
            ):
                d.tipo = tipos['194']
                d.tipo_id = 194

            elif j['id_doc_principal'] and (
                'aditivo do contrato' in j['epigrafe'].lower() or
                'aditivo de prorrogação do contrato' in j['epigrafe'].lower()
            ):
                d.tipo = tipos['195']
                d.tipo_id = 195

            elif j['id_doc_principal'] and (
                'edital de credenciamento' in j['epigrafe'].lower()
            ):
                d.tipo = tipos['196']
                d.tipo_id = 196

            elif j['id_doc_principal'] and (
                'dispensa de licitação' in j['epigrafe'].lower()
            ):
                d.tipo = tipos['197']
                d.tipo_id = 197

            elif j['id_doc_principal'] and (
                j['epigrafe'].lower().startswith('portaria')
            ):
                d.tipo = tipos['198']
                d.tipo_id = 198

            elif j['id_doc_principal'] and (
                'Demostrativo'.lower() in j['epigrafe'].lower() or
                'DEMONSTRATIVO DOS RESTOS'.lower() in j['epigrafe'].lower() or
                'Demonstrativo da Despesa com Pessoal'.lower() in j['epigrafe'].lower() or
                'Demonstrativos de Despesa com Pessoal'.lower() in j['epigrafe'].lower() or
                'Demonstrativo de Despesa'.lower() in j['epigrafe'].lower() or
                'Demonstrativo da Dívida Consolidada'.lower() in j['epigrafe'].lower() or
                'Demonstrativo da Divida Consolidada'.lower() in j['epigrafe'].lower() or
                'Demonstrativo das Garantias'.lower() in j['epigrafe'].lower() or
                'Demonstrativo das Operações'.lower() in j['epigrafe'].lower() or
                'Demonstrativo Simplificado do Relatório'.lower() in j['epigrafe'].lower() or
                'Demonstrativo da Disponibilidade de Caixa'.lower(
                ) in j['epigrafe'].lower()

            ):
                d.epigrafe = d.epigrafe.replace(
                    'DEMOSTRATIVO', 'DEMONSTRATIVO')
                d.epigrafe = d.epigrafe.replace(
                    'Demostrativo', 'Demonstrativo')
                d.old_json['epigrafe'] = d.epigrafe
                d.tipo = tipos['185']
                d.tipo_id = 185

            elif j['id_doc_principal'] and (
                'Ata de Realização do Pregão'.lower() in j['epigrafe'].lower() or
                'Ata de Realização de Pregão'.lower() in j['epigrafe'].lower() or
                'Ata de Realização Pregão'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['200']
                d.tipo_id = 200
            elif j['id_doc_principal'] and (
                'Credenciamento do Pregão'.lower() in j['epigrafe'].lower() or
                'Credenciamento de Pregão'.lower() in j['epigrafe'].lower() or
                'Credenciamento Pregão'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['201']
                d.tipo_id = 201

            elif j['id_doc_principal'] and (
                'Ata de Registro de Preço'.lower() in j['epigrafe'].lower() or
                'Ata de Registro de Preços'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['202']
                d.tipo_id = 202

            elif j['id_doc_principal'] and (
                'Edital de Intimação'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['203']
                d.tipo_id = 203

            elif j['id_doc_principal'] and (
                'Instauração de Procedimento Investigatório'.lower(
                ) in j['epigrafe'].lower()
            ):
                d.tipo = tipos['204']
                d.tipo_id = 204

            elif j['id_doc_principal'] and (
                'Proposta Pregão'.lower() in j['epigrafe'].lower() or
                'Proposta do Pregão'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['205']
                d.tipo_id = 205

            elif j['id_doc_principal'] and (
                'Ata de Reunião'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['206']
                d.tipo_id = 206

            elif j['id_doc_principal'] and (
                'Termo de Adjudicação e Homologação'.lower() in j['epigrafe'].lower() or
                'Homologação e Adjudicação'.lower() in j['epigrafe'].lower() or
                'Homologação do Processo'.lower() in j['epigrafe'].lower() or
                'Termo de Homologação'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['207']
                d.tipo_id = 207

            elif j['id_doc_principal'] and (
                'Registro de Chapa'.lower() in j['epigrafe'].lower()
            ):
                d.tipo = tipos['208']
                d.tipo_id = 208

            else:
                #em_checar += 1
                d.tipo = tipos['183']
                d.tipo_id = 183
                # if 'Adjudicação'.lower() in j['epigrafe'].lower():
                # if not j['id_doc_principal']:
                #    print(j['epigrafe'], j)

            if not d.assunto:
                d.assunto = d.epigrafe

            if not d.data_vencimento and j['data_vencimento']:
                d.data_vencimento = datetime.datetime.strptime(
                    j['data_vencimento'], "%Y-%m-%dT%H:%M:%S").astimezone()

            if j['data_alteracao']:
                d.data_ultima_atualizacao = datetime.datetime.strptime(
                    j['data_alteracao'], "%Y-%m-%dT%H:%M:%S").astimezone()

            d.save()

        print('total a checar', em_checar)

    def run__old(self):
        at = AreaTrabalho.objects.get(pk=22)
        tipo = TipoDocumentoAdministrativo.objects.get(pk=181)

        """tl_tda = {
            '25': ('PD', 'Publicações Diversas'),
        }

        tl_status = {
            '25': ('PD', 'Publicações Diversas'),
        }

        tds = Tipodoc.objects.filter(ordem__gt=0).order_by('ordem')
        for td in tds:
            print(td.id, td.ordem, td.descr)

            tls = Tipolei.objects.filter(idtipodoc=td).order_by('ordem')

            for tl in tls:
                print('---- tl:', tl.id, tl.ordem, tl.descr)
                id_str = str(tl.id)
                if id_str in tl_tda:
                    tl_tda[id_str] = TipoDocumentoAdministrativo.objects.get_or_create(
                        sigla=tl_tda[id_str][0],
                        descricao=tl_tda[id_str][1],
                        workspace_id=22
                    )
"""
        # for id_tipolei_id in tl_tda
        ds = Documento.objects.all().order_by('id')

        print('--------------------')

        print(ds.count())

        http = urllib3.PoolManager()

        for old in ds:
            # http://sislegis.camarajatai.go.gov.br/publicacoes/seeker?iddoc=2655
            # http://sislegis.camarajatai.go.gov.br/publicacoes/downloadFile.pdf?sv=2&id=2654

            # AJUSTAR NA BASE
            # 1114 1221 1222 1248
            d = DocumentoAdministrativo.objects.filter(id=old.id).first()
            if d and d.texto_integral:
                continue

            """OcrMyPDF.objects.filter(
                object_id=d.id,
                content_type=ContentType.objects.get_for_model(
                    DocumentoAdministrativo
                )
            )"""

            d = DocumentoAdministrativo()
            d.id = old.id
            d.workspace = at
            d.tipo = tipo
            d.temp_migracao_sislegis = old.id

            d.numero = old.numero
            d.ano = old.data_lei.year
            d.assunto = old.ementa

            d.data = old.data_lei
            d.assunto = old.ementa

            tipos = Assuntos.objects.filter(
                documento=old.id).values_list('tipo_id', flat=True)

            old_json = model_to_dict(old)
            old_json['tipos'] = list(tipos)

            d.old_json = old_json
            d.old_path = 'http://sislegis.camarajatai.go.gov.br/publicacoes/seeker?iddoc=%s' % old.id

            d.save()

            url = 'http://168.228.184.68:8580/publicacoes/downloadFile.pdf?sv=2&id=%s' % old.id

            request = None
            try:
                print('Download:', old.id, old.epigrafe)
                request = http.request(
                    'GET', url, timeout=600.0, retries=False)

                if not request:
                    continue

                if request.status == 404:
                    print(old.id, "não possui arquivo...")
                    continue

                if not request.data or len(request.data) == 0:
                    continue
                print('Seguindo...')

                temp = NamedTemporaryFile(delete=True)
                temp.write(request.data)
                temp.flush()

                headers = request.getheaders()
                if 'contentType' in headers:
                    ct = headers['contentType']
                else:
                    ct = headers['Content-Type']

                try:
                    name_file = 'arquivo_%s%s' % (old.id, get_extensao(ct))
                    d.texto_integral.save(name_file, File(temp), save=True)
                except Exception as e:
                    print(old.id, "Erro...", old.epigrafe, e)

            except Exception as ee:
                print(old.id, "EErro...", old.epigrafe, ee)
