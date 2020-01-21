
from datetime import datetime, timedelta
import logging
import os
from platform import node
import subprocess

from PyPDF4.pdf import PdfFileReader
from celery.worker.control import ok
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import ghostscript
from pdfrw.pdfreader import PdfReader
from prompt_toolkit.key_binding.bindings.named_commands import self_insert

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.s3_to_cmj.models import S3MateriaLegislativa
from cmj.sigad.models import Documento, VersaoDeMidia
from sapl.compilacao.models import TextoArticulado, Dispositivo
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica, AnexoNormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo


class CompressPDF:

    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }

    def compress(self, compress_level, file=None, new_file=None):

        try:
            initial_size = os.path.getsize(file)

            r = subprocess.call([
                'gs',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/prepress',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-dAutoRotatePages=/None',
                '-dCompressPages=true',
                '-dColorImageResolution=96',
                #'-dColorImageDownsampleType=/Bicubic',
                '-sOutputFile={}'.format(new_file),
                file]
            )

            final_size = os.path.getsize(new_file)
            ratio = 1 - (final_size / initial_size)
            print("Compression by {0:.0%}.".format(ratio))
            print("Final file size is {0:.1f}MB".format(
                final_size / 1000000))
            return True

        except Exception as error:
            print('Caught this error: ' + repr(error))
        except subprocess.CalledProcessError as e:
            print("Unexpected error:".format(e.output))
            return False


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)
        # self.run_busca_desordem_de_dispositivos()

        # self.run_bi()
        self.run_distibui_ocr_ao_longo_do_ano()

    def run_sql(self, sql):

        with connection.cursor() as cursor:
            cursor.execute(sql)
            # get all the rows as a list
            rows = cursor.fetchall()
            print(rows)

    def run_distibui_ocr_ao_longo_do_ano(self):
        ocrs = OcrMyPDF.objects.all().order_by('id')

        c = ocrs.count()
        d = timezone.now() - timedelta(days=365, seconds=120)
        i = 31536000 // c
        for o in ocrs:
            concluido_interval = o.concluido - o.created
            o.created = d
            o.concluido = d + concluido_interval
            o.save()

            d = d + timedelta(seconds=i)

    def run_bi(self):
        self.run_bi_files()

    def run_bi_files(self):
        models = [
            {
                'model': MateriaLegislativa,
                'file_field': 'texto_original',
                'hook': '',  # 'run_bi_files_materias_legislativas'
            },
            {
                'model': DocumentoAcessorio,
                'file_field': 'arquivo',
                'hook': ''
            },
            {
                'model': NormaJuridica,
                'file_field': 'texto_integral',
                'hook': ''
            },
            {
                'model': AnexoNormaJuridica,
                'file_field': 'anexo_arquivo',
                'hook': ''
            },
            {
                'model': DocumentoAdministrativo,
                'file_field': 'texto_integral',
                'hook': ''
            },
            {
                'model': DocumentoAcessorioAdministrativo,
                'file_field': 'arquivo',
                'hook': ''
            },
            {
                'model': DiarioOficial,
                'file_field': 'arquivo',
                'hook': ''
            },
            {
                'model': VersaoDeMidia,
                'file_field': 'file',
                'hook': 'run_bi_files_midias'
            },
        ]

        for mt in models:  # mt = metadata
            if mt['hook']:
                getattr(self, mt['hook'])
                continue
            model = mt['model']
            file = mt['file_field']
            itens = model.objects.all()
            count_pages = 0
            count_reg = 0
            for i in itens:
                path = ''
                count_reg += 1
                try:
                    ff = getattr(i, file)
                    if ff:
                        path = ff.file.name
                        pdf = PdfReader(path)
                        count_pages += len(pdf.pages)
                        ff.file.close()
                except Exception as e:
                    print(e)

                if count_reg % 100 == 0:
                    print(count_reg, model._meta.verbose_name_plural, count_pages)

            print(model._meta.verbose_name_plural, count_pages)

    def run_bi_files_materias_legislativas(self):
        pass

    def run_bi_files_midias(self):
        pass

    def run_import_check_check(self):
        materias_antigas = S3MateriaLegislativa.objects.filter(
            checkcheck=1,
            ind_excluido=0)

        for m_old in materias_antigas:
            try:
                m_new = MateriaLegislativa.objects.get(pk=m_old.cod_materia)
            except:
                pass
            else:
                m_new.checkcheck = True
                m_new.save()
                print(m_new)

    def run_testa_ghostscript(self):
        m = MateriaLegislativa.objects.get(pk=13576)

        file_path = m.texto_original.file.name

        p = CompressPDF()
        p.compress(0, file_path, file_path + '__0__new.pdf')
        #p.compress(1, file_path, file_path + '__1__new.pdf')
        #p.compress(2, file_path, file_path + '__2__new.pdf')
        #p.compress(3, file_path, file_path + '__3__new.pdf')
        #p.compress(4, file_path, file_path + '__4__new.pdf')

    def run_ajusta_datas_de_edicao_com_certidoes(self):

        # Área de trabalho pública
        docs = DocumentoAdministrativo.objects.filter(
            workspace_id=22).order_by('-id')

        for d in docs:
            c = d.certidao

            if c:
                continue

            print(d.epigrafe)

            if not d.documento_principal_set.exists():
                continue

            da = d.documento_principal_set.first()

            if da and da.documento_anexado.certidao:
                d.data_ultima_atualizacao = da.documento_anexado.certidao.created
                d.save()

    def run_busca_desordem_de_dispositivos(self):
        init = datetime.now()

        nodelist = Dispositivo.objects.filter(
            dispositivo_pai__isnull=True).order_by('ta', 'ordem')

        def busca(nl):
            numero = []

            for nd in nl:

                busca(nd.dispositivos_filhos_set.all())

                if nd.contagem_continua:
                    continue

                if not numero:
                    numero = nd.get_numero_completo()
                    continue

                if nd.get_numero_completo() < numero:
                    print(nd.ta_id, nd.ordem, nd.id, ', '.join(
                        map(str, nd.get_parents_asc())))

                numero = nd.get_numero_completo()

        busca(nodelist)
