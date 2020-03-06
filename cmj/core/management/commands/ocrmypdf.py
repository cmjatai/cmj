
from datetime import datetime, timedelta
import logging
import os
import random
import shutil
import stat
import subprocess
import threading
from time import sleep
import time

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo, \
    DocumentoAcessorioAdministrativo
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


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

            subprocess.call([
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS={}'.format(
                    self.quality[compress_level]),
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
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


class ProcessOCR(object):

    def __init__(self, cmd, logger):
        self.cmd = cmd
        self.process = None
        self.logger = logger

    def run(self, timeout):

        def target():
            self.logger.info('Thread started')
            self.process = subprocess.Popen(
                self.cmd, shell=True, stdout=subprocess.PIPE)
            self.process.communicate()
            self.logger.info('Thread finished:')

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.logger.info('Terminating process')
            self.process.terminate()
            return None
            # thread.join()

        self.logger.info(self.process.returncode)
        return self.process.returncode


class Command(BaseCommand):

    models = [
        {
            'model': DocumentoAdministrativo,
            'file_field': ('texto_integral',),
            'count': 0,
            'count_base': 9,
            'order_by': '-data'
        },
        {
            'model': DocumentoAcessorioAdministrativo,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data'
        },
        {
            'model': NormaJuridica,
            'file_field': ('texto_integral',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data'
        },
        {
            'model': DocumentoAcessorio,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data'
        },
        {
            'model': DiarioOficial,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data'
        },
        {
            'model': SessaoPlenaria,
            'file_field': ('upload_pauta', 'upload_ata', 'upload_anexo'),
            'count': 0,
            'count_base': 2,
            'order_by': '-data_inicio'
        },
        {
            'model': MateriaLegislativa,
            'file_field': ('texto_original',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data_apresentacao'
        },

    ]

    def delete_itens_tmp_folder(self):
        list = os.scandir('/tmp/')

        now = time.time()
        for i in list:
            age = now - os.stat(i.path)[stat.ST_MTIME]

            if age > 86400:
                if i.name.startswith('pymp') or\
                        i.name.startswith('com.github.ocrmypdf'):
                    shutil.rmtree(i.path, ignore_errors=True)

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.delete_itens_tmp_folder()

        init = datetime.now()

        # execução depende do crontab executado em:
        # 1,9,18,27,36,45,54 0-22 * * * djangoapps
        # /storage1/django-apps/cmj/run__commands__9min.sh

        exec_docs_antigos = init.hour < 8

        # Refaz tudo que foi feito a mais de dois anos

        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=730)).delete()

        # Refaz tudo que foi feito a mais de um mês e nao teve sucesso
        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=30),
            sucesso=False).delete()

        # OcrMyPDF.objects.filter(
        #    object_id=xxxx).delete()

        """if settings.DEBUG:
            OcrMyPDF.objects.all().delete()"""

        while self.models:

            for model in self.models:
                model['count'] = 0

            for model in self.models:
                ct = ContentType.objects.get_for_model(model['model'])
                count = 0

                data_field = model['order_by'][
                    1 if model['order_by'].startswith('-') else 0:]

                params = {
                    '{}__year__gte'.format(data_field): init.year - 1
                }
                items = model['model'].objects.filter(
                    **params).order_by(model['order_by'])

                # se não existir nenhum registro pra processar do último ano
                # ou ano atual, e a execução é de madrugada,
                # então faz do passado.
                if exec_docs_antigos and not items.exists():
                    items = model['model'].objects.order_by(model['order_by'])

                for item in items:

                    if count >= model['count_base']:
                        break

                    for ff in model['file_field']:
                        ocr = OcrMyPDF.objects.filter(
                            content_type=ct,
                            object_id=item.id,
                            field=ff).first()

                        file = getattr(item, ff)
                        if ocr and file:
                            # possui meta ocr anterior,
                            # testa se o arq é mais recente que último ocr
                            # feito
                            try:
                                t = os.path.getmtime(file.path) - 86400
                                date_file = datetime.fromtimestamp(
                                    t, timezone.utc)

                                if date_file <= ocr.created:
                                    continue
                            except Exception as e:
                                print(e)

                            # se arq é mais novo, apaga o meta ocr p fazer
                            # novamente
                            ocr.delete()
                            ocr = None

                        elif ocr and not file:
                            # se existe um meta ocr mas não existe mais o
                            # arquivo
                            ocr.delete()
                            continue

                        if not ocr and file:
                            # se existe arquivo mas não existe meta ocr por nunca
                            # ter feito ou por alguma regra de remoção acima

                            self.logger.info(
                                str(item.id) + ' ' + str(model['model']))
                            model['count'] += 1
                            print(item.id, model['model'])
                            count += 1
                            o = OcrMyPDF()
                            o.content_object = item
                            o.field = ff
                            o.sucesso = False
                            o.save()
                            try:
                                result = self.run(item, ff)
                                if result is None:
                                    return

                                o.sucesso = result
                                o.save()
                                now = datetime.now()

                                if result:
                                    post_save.send(
                                        model['model'],
                                        instance=item, using='default')

                                self.logger.info(
                                    str(now - init) + ' ' +
                                    str(item.id) + ' ' +
                                    str(model['model']))

                                if now - init > timedelta(minutes=9):
                                    return
                            except Exception as e:
                                print(e)
                            self.logger.info('Aguardando...')
                            print('Aguardando...')
                            sleep(2)
                            print('Seguindo...')
                            self.logger.info('Seguindo...')

            self.models = list(filter(lambda x: x['count'] != 0, self.models))

    def run(self, item, fstr):

        file = getattr(item, fstr)
        # não usar --force-ocr pois invalida as assinaturas digitais em
        # arquivos digitais
        # force-ocr só pode ser usado se outro teste verificar antes que um
        # documento não possui assinatura digital

        # cmd = ["ocrmypdf",  "--deskew",  "-l por", file.path, file.path]

        o_path = file.path.replace('media/sapl/', 'media/original__sapl/')
        print(o_path)
        print(file.path)

        cmd = ["ocrmypdf", "--deskew", "-l por", o_path, file.path]

        try:
            p = ProcessOCR(' '.join(cmd), self.logger)
            r = p.run(timeout=300)

            if r is None:
                return None
            if not r or r in (2, 6):
                return True
        except:
            return False

        # redo-ocr é excelente para execuções no futuro
        # mas não funciona no servidores atuais de 32 bits
        """cmd = ["ocrmypdf", "--redo-ocr", "-l por", file.path, file.path]
        try:
            p = ProcessOCR(' '.join(cmd), self.logger)
            r = p.run(timeout=300)

            if r is None:
                return None
            if not r or r == 6:
                return True
        except:
            return False
        return False"""
