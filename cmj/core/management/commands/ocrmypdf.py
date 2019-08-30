
from datetime import datetime, timedelta
import logging
import os
import random
import subprocess
import threading
from time import sleep

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


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
            'model': MateriaLegislativa,
            'file_field': ('texto_original',),
            'count': 0,
            'order_by': '-data_apresentacao'
        },
        {
            'model': NormaJuridica,
            'file_field': ('texto_integral',),
            'count': 0,
            'order_by': '-data'
        },
        {
            'model': DocumentoAcessorio,
            'file_field': ('arquivo',),
            'count': 0,
            'order_by': '-data'
        },
        {
            'model': DiarioOficial,
            'file_field': ('arquivo', ),
            'count': 0,
            'order_by': '-data'
        },
        {
            'model': SessaoPlenaria,
            'file_field': ('upload_pauta', 'upload_ata', 'upload_anexo'),
            'count': 0,
            'order_by': '-data_inicio'
        },
        {
            'model': DocumentoAdministrativo,
            'file_field': ('texto_integral', ),
            'count': 0,
            'order_by': '-data'
        },
        {
            'model': DocumentoAcessorioAdministrativo,
            'file_field': ('arquivo', ),
            'count': 0,
            'order_by': '-data'
        },
    ]

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        init = datetime.now()

        # Refaz tudo que foi feito a mais de um ano
        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=365)).delete()

        # Refaz tudo que foi feito a mais de um mês e nao teve sucesso
        OcrMyPDF.objects.filter(
            created__lt=init - timedelta(days=30),
            sucesso=False).delete()

        while self.models:

            for model in self.models:
                model['count'] = 0

            for model in self.models:
                ct = ContentType.objects.get_for_model(model['model'])
                count = 0
                for item in model['model'].objects.order_by(model['order_by']):
                    if count >= 3:
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
                            t = os.path.getmtime(file.path)
                            date_file = datetime.fromtimestamp(t, timezone.utc)

                            if date_file <= ocr.created:
                                continue
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
                            result = self.run(item, ff)
                            if result is None:
                                return

                            o.sucesso = result
                            o.save()
                            now = datetime.now()

                            if result:
                                item.save()

                            self.logger.info(
                                str(now - init) + ' ' +
                                str(item.id) + ' ' +
                                str(model['model']))

                            if now - init > timedelta(minutes=9):
                                return
                            self.logger.info('Aguardando...')
                            sleep(10)
                            self.logger.info('Seguindo...')

            self.models = list(filter(lambda x: x['count'] != 0, self.models))

    def run(self, item, fstr):

        file = getattr(item, fstr)

        cmd = ["ocrmypdf",  "--deskew", file.path, file.path]

        try:
            p = ProcessOCR(' '.join(cmd), self.logger)
            r = p.run(timeout=300)

            if r is None:
                return None

            if not r or r == 6:  # 6 = resposta para pdf que já possui texto
                return True
        except:
            return False
        return False

    def run_old(self, item, fstr):

        file = getattr(item, fstr)

        cmd = ["ocrmypdf",  "--deskew", file.path, file.path]
        try:
            proc = subprocess.run(
                cmd,
                timeout=60,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            result = proc.stdout
            if proc.returncode == 6:
                #print("Skipped document because it already contained text")
                pass
            elif proc.returncode == 0:
                #print("OCR complete")
                return True
        except:
            pass
        return False
