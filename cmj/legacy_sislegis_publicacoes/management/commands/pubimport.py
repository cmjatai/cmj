
from datetime import timedelta
import datetime
import mimetypes

from django.contrib.auth import get_user_model
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
from cmj.legacy_sislegis_publicacoes.models import Tipodoc, Tipolei, Documento,\
    Assuntos
from sapl.protocoloadm.models import TipoDocumentoAdministrativo,\
    DocumentoAdministrativo, Anexado, TramitacaoAdministrativo
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

    def handle(self, *args, **options):

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run()
        self.reset_id_model(CertidaoPublicacao)

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

    def run(self):
        at = AreaTrabalho.objects.get(pk=22)

        clear = False

        if clear:
            a = Anexado.objects.all()
            a.filter(documento_principal__workspace=at)
            a.delete()

        docs = DocumentoAdministrativo.objects.filter(
            workspace=at).order_by('-id')

        print(docs.count())

        em_checar = 0

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
                d.save()

            # Balancetes Contábeis
            elif 25 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['183']
                d.save()
            elif 29 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['184']
                d.save()
            elif 8 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['185']
                d.save()
            elif 35 in j['tipos'] and len(j['tipos']) == 1:
                d.tipo = tipos['186']
                d.save()
            elif 38 in j['tipos'] and len(j['tipos']) == 1 and not j['id_doc_principal']:
                d.tipo = tipos['187']
                d.tipo_id = 187
                d.tramitacao = True
                d.save()

                d.tramitacaoadministrativo_set.all().delete()
                for anexo in d.documento_principal_set.all().order_by('-id'):
                    t = TramitacaoAdministrativo()
                    t.status_id = 4
                    t.documento = d
                    if anexo.documento_anexado.certidao:
                        t.data_tramitacao = anexo.documento_anexado.certidao.created.date()
                    else:
                        t.data_tramitacao = anexo.documento_anexado.data
                    t.unidade_tramitacao_local_id = 3
                    t.unidade_tramitacao_destino_id = 3
                    t.texto = 'Publicação de: %s' % anexo.documento_anexado
                    t.save()
                    print(anexo)

            else:
                em_checar += 1
                if j['tipos']:
                    print(j)

        print("sem classificação não impressos")
        print('total a checar', em_checar)

    def run__base(self):
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
