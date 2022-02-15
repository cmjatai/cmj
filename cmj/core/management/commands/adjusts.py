import glob
import logging
import os
import subprocess
import sys

from PIL import Image, ImageFilter
import cv2
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.signals import Manutencao
from cmj.utils import ProcessoExterno
import numpy as np
from sapl.compilacao.models import TextoArticulado, Dispositivo
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        folder_in = '/home/leandro/TEMP/scanners/'
        folder_out = folder_in + 'out/'
        os.makedirs(folder_out, exist_ok=True)

        lf = glob.glob(folder_in + '**', recursive=True)
        lf.sort()

        flist_out = []

        composicao = [
            ['out-0451', 'out-0538'],
            # ['out-0533', 'out-0538']
        ]

        for c in composicao:
            for f in lf:
                if c[0] and c[0] not in f:
                    continue
                c[0] = ''

                flist_out.append(f)
                if c[1] in f:
                    break

        doc = SimpleDocTemplate(
            folder_out + 'out.pdf',
            rightMargin=0,
            leftMargin=0,
            topMargin=0,
            bottomMargin=0)

        c = canvas.Canvas(folder_out + 'out.pdf')

        """def get_white_noise_image(w, h):
            pil_map = Image.fromarray(np.random.randint(
                0, 255, (w, h, 3), dtype=np.dtype('uint8')))
            return pil_map"""

        for f in flist_out:
            if folder_out in f:
                continue

            # if '.png' not in f:
            #    continue

            if '.jpeg' not in f.lower() and '.jpg' not in f.lower():
                continue

            f_out = f.split(folder_in)
            f_out = folder_out.join(f_out)
            print(f, f_out)

            #f_out = f_out.replace('.png', '.jpeg')

            try:
                """i = Image.open(f)
                i = i.convert("L")
                i = np.array(i)
                i = (i > 128) * 255
                #i = Image.fromarray(i).convert("L")
                i = Image.fromarray(np.uint8(i))
                i.save(f_out, optimize=True, quality=5)"""

                #img = Image.open(f)
                #img = img.convert("L")
                # img.save(f_out)  # , optimize=True, quality=10)"""

                i = cv2.imread(f)
                ig = cv2.cvtColor(i, cv2.COLOR_RGB2GRAY)
                #ig = cv2.inRange(ig, 200, 255)
                cv2.imwrite(
                    f_out, ig, [
                        int(cv2.IMWRITE_JPEG_QUALITY), 20,
                        int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
                    ])

                c.drawImage(f_out, 0, 0,
                            width=595,
                            height=841)
                c.showPage()
            except Exception as e:
                continue
        c.save()
        """
        cria pdf através da pillow
        
        flist_out_img_obj = []
        for f in flist_out:
            flist_out_img_obj.append(Image.open(f))

        f = flist_out_img_obj.pop(0)

        f.save(
            folder_out + 'out.pdf',
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=flist_out_img_obj)"""

        cmd = ["{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
               "-q",                  # Execução silenciosa
               "-l por",              # tesseract portugues
               "-j {}".format(8),     # oito threads
               "--fast-web-view 0",   # não inclui fast web view
               "--image-dpi 300",
               #"--rotate-pages",
               "--remove-background",

               "--optimize 3",
               "--jpeg-quality 5",

               # "--deskew",
               #"--clean-final",
               "--pdfa-image-compression jpeg",  # jpeg
               "--output-type pdfa-1",
               #"--tesseract-timeout 0",
               folder_out + 'out.pdf',
               folder_out + 'out_ocr.pdf']

        print(' '.join(cmd))
        # subprocess.Popen(
        #    ' '.join(cmd), shell=True, stdout=subprocess.PIPE)
        try:
            p = ProcessoExterno(' '.join(cmd), self.logger)
            r = p.run(timeout=300)

            if r is None:
                return
            if not r or r in (2, 6):
                return
        except:
            return

        """try:
                i = Image.open(f)
                i.convert(mode='P', palette=Image.W)
    
                #f_out = f_out.replace('jpeg', 'png')
                #f_out = f_out.replace('jpg', 'png')
    
                i.save(f_out)
                break
    
            except IsADirectoryError:
                os.makedirs(f_out, exist_ok=True)"""

    def transforma_imagens_armazenadas_em_pdf(self):
        models = [
            {
                'model': MateriaLegislativa,
                'file_field': ('texto_original',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data_apresentacao',
                'years_priority': 0
            },
            {
                'model': DocumentoAdministrativo,
                'file_field': ('texto_integral',),
                'count': 0,
                'count_base': 9,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DocumentoAcessorioAdministrativo,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': NormaJuridica,
                'file_field': ('texto_integral',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DocumentoAcessorio,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DiarioOficial,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': SessaoPlenaria,
                'file_field': ('upload_pauta', 'upload_ata', 'upload_anexo'),
                'count': 0,
                'count_base': 2,
                'order_by': '-data_inicio',
                'years_priority': 0
            },

        ]

        for md in models:

            m = md['model']

            q = Q()
            for f in md['file_field']:
                param = {f'{f}__iendswith': '.jpeg'}
                q |= Q(**param)
                param = {f'{f}__iendswith': '.jpg'}
                q |= Q(**param)
                param = {f'{f}__iendswith': '.png'}
                q |= Q(**param)

            qs = m.objects.filter(q)

            ct = ContentType.objects.get_for_model(m)
            for i in qs:
                if not OcrMyPDF.objects.filter(content_type=ct, object_id=i.id).exists():
                    OcrMyPDF.objects.filter(
                        content_type=ct, object_id=i.id).delete()

                for f in md['file_field']:
                    p = getattr(i, f)
                    if p:
                        print(i.id, f, p.path)

                        inn = p.path.replace(
                            'media/sapl/', 'media/original__sapl/')
                        inn = inn.replace('media/cmj/', 'media/original__cmj/')

                        out = inn.split('.')
                        out[-1] = 'pdf'
                        out = '.'.join(out)

                        temp_out = f'/tmp/{out.split("/")[-1]}'

                        img = Image.open(inn)
                        try:
                            dx, dy = img.info['dpi']
                        except:
                            dx, dy = 100, 100

                        img.convert('RGB')
                        img.save(temp_out, resolution=dx)

                        destino = os.path.basename(temp_out)

                        with open(temp_out, 'rb') as f_in:
                            p.save(destino, File(f_in), save=True)

                        print(p.path)
                        print(p.original_path)
