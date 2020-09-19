
from datetime import datetime, timedelta
import logging
import os
from pwd import getpwuid
import shutil
import stat
import subprocess
from time import sleep
import time

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.utils import ProcessoExterno
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


class Command(BaseCommand):

    max_paginas_noturno = 100  # avaliar tempo de execução para números maiores
    max_paginas_diurno = 50

    # só usa os limites de tamanho de arquivo se não houver número de páginas
    max_size_noturno = 20 * 1024 * 1024
    max_size_diurno = 5 * 1024 * 1024

    models = [
        {
            'model': MateriaLegislativa,
            'file_field': ('texto_original',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data_apresentacao',
            'years_priority': 20
        },
        {
            'model': DocumentoAdministrativo,
            'file_field': ('texto_integral',),
            'count': 0,
            'count_base': 9,
            'order_by': '-data',
            'years_priority': 20
        },
        {
            'model': DocumentoAcessorioAdministrativo,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data',
            'years_priority': 20
        },
        {
            'model': NormaJuridica,
            'file_field': ('texto_integral',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data',
            'years_priority': 20
        },
        {
            'model': DocumentoAcessorio,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data',
            'years_priority': 20
        },
        {
            'model': DiarioOficial,
            'file_field': ('arquivo',),
            'count': 0,
            'count_base': 2,
            'order_by': '-data',
            'years_priority': 20
        },
        {
            'model': SessaoPlenaria,
            'file_field': ('upload_pauta', 'upload_ata', 'upload_anexo'),
            'count': 0,
            'count_base': 2,
            'order_by': '-data_inicio',
            'years_priority': 20
        },

    ]

    def delete_itens_tmp_folder(self):
        list = os.scandir('/tmp/')

        now = time.time()
        for i in list:
            age = now - os.stat(i.path)[stat.ST_MTIME]

            clears = [
                ('djangoapps', 'pymp'),
                ('djangoapps', 'com.github.ocrmypdf'),
                ('djangoapps', 'yarn--'),
                #('solr', 'upload_'),
                ('djangoapps', 'br.leg.go.jatai.portalcmj.')
            ]

            if age > 86400:
                for user, start_name in clears:
                    if i.name.startswith(start_name):
                        if getpwuid(os.stat(i.path).st_uid).pw_name == user:
                            try:
                                shutil.rmtree(i.path, ignore_errors=True)
                                if os.path.exists(i.path):
                                    os.remove(i.path)
                                break
                            except Exception as e:
                                print(e)
                                break

    def is_running(self):
        process = subprocess.Popen(
            ['ps', '-eo', 'pid,args'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        mypid = str(os.getpid())
        stdout, notused = process.communicate()
        for line in stdout.splitlines():
            line = line.decode("utf-8")
            pid, cmdline = line.split(' ', 1)

            if pid == mypid:
                continue

            if 'manage.py ocrmypdf' in cmdline:
                return True

        return False

    def handle(self, *args, **options):

        init = datetime.now()
        if not settings.DEBUG and self.is_running():
            print(init, 'Command OcrMyPdf já está sendo executado por outro processo')
            return

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.delete_itens_tmp_folder()

        # execução depende do crontab executado em:
        # 1,9,18,27,36,45,54 0-22 * * * djangoapps
        # /storage1/django-apps/cmj/run__commands__9min.sh

        execucao_noturna = init.hour < 6 or init.hour >= 22

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
                    '{}__year__gte'.format(data_field): init.year - model['years_priority']
                }
                items = model['model'].objects.filter(
                    **params).order_by(model['order_by'])

                # se não existir nenhum registro pra processar do último ano
                # ou ano atual, e a execução é de madrugada,
                # então faz do passado.
                if execucao_noturna and not items.exists():
                    items = model['model'].objects.order_by(model['order_by'])

                #items = items.filter(pk=86)
                for item in items:

                    # item.save()
                    paginas = 0
                    if hasattr(item, '_paginas'):
                        # tenta capturar o número de páginas
                        try:
                            paginas = item.paginas
                        except:
                            paginas = 0

                        # se não tem conseguiu num de páginas
                        # só passa ao teste de tamanho de arquivo se a execução
                        # é noturna
                        if not paginas and not execucao_noturna:
                            continue

                        # mesmo a execução sendo noturna não faz arquivos com
                        # mais de max_paginas_noturno
                        if paginas > self.max_paginas_noturno:
                            continue

                        # se diurno não faz ocr em arquivos com páginas
                        # superiores a max_paginas_diurno
                        if paginas > self.max_paginas_diurno and not execucao_noturna:
                            continue

                    if count >= model['count_base']:
                        break

                    for ff in model['file_field']:

                        # se documento foi homologado não executa ocr
                        if hasattr(item, 'metadata'):
                            md = item.metadata
                            if md and 'signs' in md and ff in md['signs']:
                                if 'hom' in md['signs'][ff] and\
                                        md['signs'][ff]['hom']:
                                    continue

                        file = getattr(item, ff)

                        if file and not file.name.endswith('.pdf'):
                            continue

                        if not paginas:
                            if file and file.name and file.size > self.max_size_noturno:
                                continue

                            if file and file.name and file.size > self.max_size_diurno and not execucao_noturna:
                                continue

                        ocr = OcrMyPDF.objects.filter(
                            content_type=ct,
                            object_id=item.id,
                            field=ff).first()

                        if ocr and file and file.name:
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

                        elif ocr and not file or ocr and file and not file.name:
                            # se existe um meta ocr mas não existe mais o
                            # arquivo
                            ocr.delete()
                            continue

                        if not ocr and file and file.name:
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
                                init_item = datetime.now()
                                result = self.run(item, ff)
                                if result is None:
                                    return

                                o.sucesso = result
                                o.save()
                                now = datetime.now()

                                if hasattr(item, '_paginas'):
                                    print(
                                        item.id,
                                        item._paginas,
                                        model['model']._meta.label,
                                        str(now - init_item)
                                    )

                                if result:
                                    post_save.send(
                                        model['model'],
                                        instance=item, using='default')

                                self.logger.info(
                                    str(now - init_item) + ' ' +
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
        o_path = o_path.replace('media/cmj/', 'media/original__cmj/')
        # print(o_path)
        # print(file.path)

        cmd = ["ocrmypdf",
               "--deskew",
               "-l por",
               "--output-type pdfa-1",
               o_path, file.path]

        try:
            p = ProcessoExterno(' '.join(cmd), self.logger)
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
