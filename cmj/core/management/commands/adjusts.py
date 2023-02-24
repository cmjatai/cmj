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
import fitz
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.utils import Manutencao
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
        post_save.disconnect(dispatch_uid='timerefresh_post_signal')
        self.logger = logging.getLogger(__name__)

        m = MateriaLegislativa.objects.get(pk=19819)
        m.texto_original.shorten_file_name()

        # self.transformar_pdfs_em_imagens()
        return
        self.criar_pdfs()

    def transformar_pdfs_em_imagens(self, *args, **options):
        folder_raiz = '/home/leandro/TEMP/scanners/'

        folder_in_pdfs = folder_raiz + 'in_pdfs/'
        folder_in_images = folder_raiz + 'in_images/'

        os.makedirs(folder_in_images, exist_ok=True)

        lfpdf = glob.glob(glob.escape(folder_in_pdfs) + '**', recursive=True)
        lfpdf.sort()

        for f in lfpdf:

            fimg_out = f.replace('in_pdfs', 'in_images')
            if not f.endswith('.pdf'):
                os.makedirs(fimg_out, exist_ok=True)
                continue

            doc = fitz.open(f)

            for index, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                pix.save(f'{fimg_out}-{index:0>6}.png')
        return

    def criar_pdfs(self, *args, **options):
        folder_raiz = '/home/leandro/TEMP/scanners/'

        folder_in_images = folder_raiz + 'in_images/'

        os.makedirs(folder_in_images, exist_ok=True)
        os.makedirs(folder_in_images.replace(
            'in_images', 'out_images'), exist_ok=True)

        lfimagens = glob.glob(glob.escape(
            folder_in_images) + '**', recursive=True)
        lfimagens.sort()

        for ipath in lfimagens:
            if ipath.endswith('.png'):
                continue
            # print(f"'{ipath}',")
            pass

        arquivos_d_saida = [
            [
                '/home/leandro/TEMP/scanners/in_images/OFICIO DE ENCAMINHAMENTO E PARECER CI',
                '/home/leandro/TEMP/scanners/in_images/OFICIO DE ENCAMINHAMENTO E PARECER CI/OFÍCIO ENCAMINHAMENTO DAS CONTAS 2022',
                '/home/leandro/TEMP/scanners/in_images/OFICIO DE ENCAMINHAMENTO E PARECER CI/PARECER',
                '/home/leandro/TEMP/scanners/in_images/OFICIO DE ENCAMINHAMENTO E PARECER CI/DECLARAÇÕES ART.1º, b, IV E VII IN 0012023',
                '/home/leandro/TEMP/scanners/in_images/APLICAÇÕES',
            ],
        ]
        conjunto = [
            [
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/DEMONSTRATIVO SUBSÍDIOS VEREADORES',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA JANEIRO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA FEVEREIRO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA MARÇO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA ABRIL',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA MAIO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA JUNHO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA JULHO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA AGOSTO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA SETEMBRO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA OUTUBRO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA NOVEMBRO',
                '/home/leandro/TEMP/scanners/in_images/SUBSIDIOS VEREADORES E SECRETARIO GERAL/FOLHA VEREADORES/FOLHA DEZEMBRO',
            ],
            [
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/CERTIDÃO NEGATIVA DE DÉBITO RPPS',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/DEMONSTRATIVO ART. 1º, b, II da IN 0012023',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/LEIS RPPS 2022',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS JANEIRO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS FEVEREIRO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS MARÇO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS ABRIL',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS MAIO',
            ],
            [
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS JUNHO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS JULHO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS AGOSTO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS SETEMBRO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS OUTUBRO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS NOVEMBRO',
                '/home/leandro/TEMP/scanners/in_images/RPPS E FOLHAS/RPPS DEZEMBRO',
            ],
            [
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO JANEIRO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO FEVEREIRO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO MARÇO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO ABRIL',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO MAIO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO JUNHO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO JULHO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO AGOSTO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO SETEMBRO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO OUTUBRO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO NOVEMBRO',
                '/home/leandro/TEMP/scanners/in_images/EXTRATOS 2022/EXTRATO DEZEMBRO',
            ],
        ]

        for index, folders_in in enumerate(arquivos_d_saida):

            pages_out = []

            for fdIn in folders_in:
                lfpdf = glob.glob(glob.escape(fdIn) + '/*.png', recursive=True)
                lfpdf.sort()
                pages_out += lfpdf

            folder_out = folders_in[0].replace('in_images', 'out')

            doc = SimpleDocTemplate(
                folder_out + f'{index}.pdf',
                rightMargin=0,
                leftMargin=0,
                topMargin=0,
                bottomMargin=0)

            c = canvas.Canvas(folder_out + f'out{index}.pdf')

            """def get_white_noise_image(w, h):
                pil_map = Image.fromarray(np.random.randint(
                    0, 255, (w, h, 3), dtype=np.dtype('uint8')))
                return pil_map"""

            for f in pages_out:
                if folder_out in f:
                    continue

                # if '.png' not in f:
                #    continue

                # if '.jpeg' not in f.lower() and '.jpg' not in f.lower():
                #    continue

                f_out_image = f.replace('in_image', 'out_image')
                os.makedirs(
                    '/'.join(f_out_image.split('/')[:-1]), exist_ok=True)
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

                    def adjust_contrast_brightness(img, contrast: float=1.0, brightness: int=0):
                        """
                        Adjusts contrast and brightness of an uint8 image.
                        contrast:   (0.0,  inf) with 1.0 leaving the contrast as is
                        brightness: [-255, 255] with 0 leaving the brightness as is
                        """
                        brightness += int(round(255 * (1 - contrast) / 2))
                        return cv2.addWeighted(img, contrast, img, 0, brightness)

                    i = cv2.imread(f)
                    ig = cv2.cvtColor(i, cv2.COLOR_RGB2GRAY)
                    ig = adjust_contrast_brightness(ig, 1.1, 0)
                    cv2.imwrite(
                        f_out_image, ig, [
                            int(cv2.IMWRITE_JPEG_QUALITY), 100,
                            #int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1,
                            #int(cv2.IMWRITE_PNG_COMPRESSION), 9
                        ])

                    c.drawImage(f_out_image, 0, 0,
                                width=595,
                                height=841)
                    c.showPage()
                    # c.save()
                    # return
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
                   #"-q",                  # Execução silenciosa
                   "-l por",              # tesseract portugues
                   "-j 8",     # oito threads
                   "--fast-web-view 10000000",   # não inclui fast web view
                   "--image-dpi 300",
                   #"--rotate-pages",
                   #"--remove-background",

                   "--optimize 0",
                   "--jpeg-quality 100",
                   "--png-quality 100",
                   #"--jbig2-lossy",

                   # "--deskew",
                   #"--clean-final",
                   "--pdfa-image-compression jpeg",  # jpeg  lossless
                   "--output-type pdfa-1",
                   #"--tesseract-timeout 0",
                   f'"{folder_out}out{index}.pdf"',
                   f'"{folder_out}out_ocr{index}.pdf"']

            print(' '.join(cmd))
            subprocess.Popen(
                ' '.join(cmd), shell=True, stdout=subprocess.PIPE)
            # try:
            #    p = ProcessoExterno(' '.join(cmd), self.logger)
            #    r = p.run(timeout=300)#

            #    if r is None:
            #        return
            #    if not r or r in (2, 6):
            #        return
            # except:
            #    return

        """try:
                i = Image.open(f)
                i.convert(mode='P', palette=Image.W)

                #f_out = f_out.replace('jpeg', 'png')
                #f_out = f_out.replace('jpg', 'png')

                i.save(f_out)
                break

            except IsADirectoryError:
                os.makedirs(f_out, exist_ok=True)"""
