
from pathlib import Path
import glob
import io
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
from PIL.Image import LANCZOS, Resampling
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from pytesseract.pytesseract import Output
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate
import cv2
import fitz
import ocrmypdf

from cmj.arq.models import ArqDoc
from cmj.arq.tasks import console
from cmj.utils import Manutencao
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.rules.apps import reset_id_model
import numpy as np
import pytesseract as tess


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


def img_replace(page, xref, filename=None, stream=None, pixmap=None):

    doc = page.parent
    new_xref = page.insert_image(
        page.rect, filename=filename, stream=stream, pixmap=pixmap
    )
    doc.xref_copy(new_xref, xref)
    last_contents_xref = page.get_contents()[-1]
    doc.update_stream(last_contents_xref, b" ")


def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened


def increase_brightness(img, value):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        m = Manutencao()
        m.desativa_auto_now()
        m.desativa_signals()

        self.folder_raiz = '/home/leandrojatai/TEMP/oficio/'

        # self.process0() # renomeia meses por extenso para formato yy-mm
        # self.pdf2png()  # converte todas as páginas de todos pdfs para pgn em in_images
        self.process1()  # cria copia de in_images em in1_images aplic brilho e contraste e convertendo para '1'
        # self.process2()  # monta pdf com imagens de in_images
        # self.process3(f'"{self.folder_raiz}out.pdf"', f'"{self.folder_raiz}out_ocr_1.pdf"')  # executa ocrmypdf no pdf grande gerado em processo2
        self.process4()  # remonta pdf com imagens geradas em processo1

        self.process3(f'"{self.folder_raiz}out_ocr_2.pdf"', f'"{self.folder_raiz}out_ocr_3.pdf"')  # executa ocrmypdf no pdf gerado em processo4

    def process4(self, *args, **options):

        f_images = self.folder_raiz + 'in1_images/'

        imgs = glob.glob(glob.escape(f_images) + '**', recursive=True)
        imgs.sort()

        doc_out = self.folder_raiz + 'out_ocr_2.pdf'
        doc_in = fitz.open(self.folder_raiz + 'out_ocr_1.pdf')

        ipage = 0
        for i, f in enumerate(imgs):

            if not f.endswith('.png'):
                continue

            page = doc_in[ipage]
            ipage += 1

            xref = page.get_image_info(xrefs=True)[0]['xref']
            page.delete_image(xref)
            page.replace_image(xref=xref, filename=f)

        doc_in.save(doc_out)
        doc_in.close()

    def process3(self, fin, fout):

        cmd = ["{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
               #"-q",                  # Execução silenciosa
               "-l por",              # tesseract portugues
               "-j 20",  # 20 threads
               #"--fast-web-view 10000000",   # não inclui fast web view
               #"--image-dpi 300",
               # "--rotate-pages",
               # "--remove-background",

               "--optimize 3",
               #"--jpeg-quality 100",
               #"--png-quality 100",
               #"--jbig2-lossy",
               # "--skip-text",
               # "--deskew",
               #"--clean-final",
               #"--pdfa-image-compression jpeg",  # jpeg  lossless
               "--output-type pdfa-2",
               #"--tesseract-timeout 0",
               fin,
               fout]

        print(' '.join(cmd))
        return
        r = console(' '.join(cmd))
        print(r[0])
        print(r[1].decode('utf-8'))
        print(r[2].decode('utf-8'))

        # subprocess.Popen(
        #    ' '.join(cmd), shell=True, stdout=subprocess.PIPE)

    def process2(self, *args, **options):

        f_images = self.folder_raiz + 'in_images/'

        imgs = glob.glob(glob.escape(f_images) + '**', recursive=True)
        imgs.sort()

        doc_out = fitz.open()

        for i, f in enumerate(imgs):

            if not f.endswith('.png'):
                continue

            img = fitz.open(f)
            rect = img[0].rect  # pic dimension
            pdfbytes = img.convert_to_pdf()  # make a PDF stream
            img.close()  # no longer needed
            imgPDF = fitz.open("pdf", pdfbytes)  # open stream as PDF

            # w = 595
            # h = 842
            # if rect.width > rect.height:
            #    h = w
            #    w = 842
            # page = doc_out.new_page(width=w,  height=h)
            page = doc_out.new_page(width=rect.width, height=rect.height)

            page.show_pdf_page(rect, imgPDF, 0)  # image fills the page

        doc_out.save(self.folder_raiz + 'out.pdf', garbage=4, pretty=True,
                     deflate=True, deflate_images=True,
                     clean=True)

    def process1(self, *args, **options):

        f_images = self.folder_raiz + 'in_images/'

        imgs = glob.glob(glob.escape(f_images) + '**', recursive=True)
        imgs.sort()

        for i, f in enumerate(imgs):
            print(i, f)

            fimg_out = f.replace('in_images', 'in1_images')
            if not f.endswith('.png'):
                os.makedirs(fimg_out, exist_ok=True)
                continue

            img = Image.open(f)

            # enhancer = ImageEnhance.Sharpness(img)
            # img = enhancer.enhance(1.5)

            # img = img.convert('L')

            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)

            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)

            img = img.convert('1')

            # img = img.filter(ImageFilter.EDGE_ENHANCE)
            img.save(fimg_out)


    def pdf2png(self, *args, **options):

        f_in_pdfs = self.folder_raiz + 'in_pdfs/'

        scanners = glob.glob(glob.escape(f_in_pdfs) + '**', recursive=True)
        scanners.sort()

        for i, f in enumerate(scanners):

            print(i, f)

            fimg_out = f.replace('in_pdfs', 'in_images')
            if not f.endswith('.pdf'):
                os.makedirs(fimg_out, exist_ok=True)
                continue

            doc = fitz.open(f)

            for index, page in enumerate(doc):

                # page.set_rotation(180)
                out_img = f'{fimg_out}-{index:0>6}.png'

                if os.path.exists(out_img):
                    continue

                pix = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY)
                pix.save(out_img)

                continue

                im = Image.open(out_img)

                im_meta = tess.image_to_osd(im, output_type=Output.DICT)

                if not im_meta['rotate']:
                    continue

                im = im.rotate(360 - im_meta['rotate'], resample=LANCZOS, expand=True)
                im.save(out_img, dpi=(300, 300))


    def process0(self, *args, **options):
        # possui erro em renomeação de subpastas

        f_in_pdfs = self.folder_raiz + 'in_pdfs/'

        scanners = glob.glob(glob.escape(f_in_pdfs) + '**', recursive=True)
        scanners.sort()

        meses = {
            'JANEIRO': '24-01',
            'FEVEREIRO': '24-02',
            'MARÇO': '24-03',
            'ABRIL': '24-04',
            'MAIO': '24-05',
            'JUNHO': '24-06',
            'JULHO': '24-07',
            'AGOSTO': '24-08',
            'SETEMBRO': '24-09',
            'OUTUBRO': '24-10',
            'NOVEMBRO': '24-11',
            'DEZEMBRO': '24-12',
        }

        errors = []

        for i, f in enumerate(scanners):

            if f.endswith('.pdf'):
                continue

            print(i, f)
            fn = f
            for k, v in meses.items():
                fn = fn.replace(k, v)

            if f == fn:
                continue

            try:
                os.rename(f, fn)
            except:
                errors.append((f, fn))

        for f, fn in errors:
            os.rename(f, fn)

    def criar_pdfs__simone(self, *args, **options):
        folder_raiz = '/home/leandro/TEMP/CI/'

        folder_scanners = folder_raiz + 'scanner/'

        folder_in_images = folder_raiz + 'in_images/'
        folder_out_images = folder_raiz + 'out_images/'

        os.makedirs(folder_in_images, exist_ok=True)
        os.makedirs(folder_out_images, exist_ok=True)

        scanners = glob.glob(glob.escape(
            folder_scanners) + '**', recursive=True)
        scanners.sort()

        for ipath in scanners:
            if ipath.endswith('.png'):
                continue
            # print(f"'{ipath}',")
            pass

        arquivos_d_saida = [
            [
                '/home/leandro/TEMP/CI/in_images/out',
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

    def pdftopdfa(self):
        folder_in = '/home/leandro/Downloads/leyse/'

        folder_out = folder_in + 'out_pdfa/'
        os.makedirs(folder_out, exist_ok=True)

        lfpdf = glob.glob(glob.escape(folder_in) + '**', recursive=True)
        lfpdf.sort()

        for f in lfpdf:

            if 'out_pdfa' in f:
                continue

            fout = f.replace(folder_in, folder_out)
            if '.pdf' not in f:
                os.makedirs(fout, exist_ok=True)
                continue

            cmd = ["{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
                   #"-q",                  # Execução silenciosa
                   "-l por",              # tesseract portugues
                   "-j 8",     # oito threads
                   #"--fast-web-view 10000000",   # não inclui fast web view
                   #"--image-dpi 300",
                   #"--rotate-pages",
                   #"--remove-background",
                   "--force-ocr",
                   #"--optimize 0",
                   #"--jpeg-quality 100",
                   #"--png-quality 100",
                   #"--jbig2-lossy",

                   # "--deskew",
                   #"--clean-final",
                   #"--pdfa-image-compression jpeg",  # jpeg  lossless
                   "--output-type pdfa-2",
                   #"--tesseract-timeout 0",
                   f'"{f}"',
                   f'"{fout}"']

            print(' '.join(cmd))
            p = subprocess.Popen(
                ' '.join(cmd), shell=True, stdout=subprocess.PIPE)
            p.wait()
            #subprocess.call(' '.join(cmd))
