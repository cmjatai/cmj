
from collections import OrderedDict
import glob
import io
import logging
import os
from pathlib import Path
import pathlib
import re
import subprocess
import sys
from time import sleep

from PIL import Image, ImageEnhance, ImageDraw
from PIL.Image import Resampling
from bs4 import BeautifulSoup as bs
import cv2
from django.apps import apps
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
import fitz
import ocrmypdf
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate
import requests

from cmj.arq.models import ArqDoc
from cmj.utils import Manutencao
from cmj.videos.tasks import task_pull_youtube_upcoming
import numpy as np
from sapl.compilacao.models import TextoArticulado, Dispositivo,\
    UrlizeReferencia
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.rules.apps import reset_id_model


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

        # self.get_all_tas()

        return
        ds = Dispositivo.objects.filter(
            ta_publicado_id=9665).order_by('ordem')

        for d in ds:
            d.visibilidade = False
            d.save()
            print(d)

        return
        # abre autografo 1193, captura tabelas do anexo iii e adiciona em seus
        # dispositivos
        html_file = open('/home/leandro/Downloads/702/aut.html', 'r').read()

        soup = bs(html_file, "html.parser")

        tables = list(soup.find_all("table"))[-5:]

        # for t in tables:
        #    print(t)

        ds = Dispositivo.objects.filter(
            ta_id=9665,
            dispositivo_raiz_id=198029, id__gt=198030).order_by('ordem')

        ti = 0
        for d in ds:
            if d.texto and 'table' not in d.texto:
                continue

            t = tables[ti]
            ti += 1

            str_t = str(t)
            t = str_t.replace('<tr></tr>\n', '')

            st = f'CDS-{ti}<br>{t}<br>'

            d.texto = st
            d.save()

        return

        # abre autografo 1193, captura textos do anexo ii e adiciona em seus
        # dispositivos
        html_file = open(
            '/home/leandro/Downloads/702/aut_anexo2.html', 'r').read()

        soup = bs(html_file, "html.parser")

        tagsp = list(soup.find_all("p"))

        # for t in tables:
        #    print(t)

        ds = Dispositivo.objects.filter(
            ta_id=9665,
            dispositivo_raiz_id=197312, id__gt=197313).order_by('ordem')

        # for d in ds.filter(texto=''):
        #    print(d)
        # return

        for p in tagsp:
            tagb = p.contents[0]

            if not hasattr(tagb, 'contents') or not tagb.contents or not len(tagb.contents):
                continue

            sb = str(tagb.contents[0]).split(' ')

            if not len(sb):
                continue

            d = ds.filter(rotulo=sb[0]).first()
            if not d:
                continue

            str_p = str(p)

            str_p = str_p.replace(sb[0], '', 1)
            str_p = str_p.replace('<p>', '')
            str_p = str_p.replace('</p>', '')
            str_p = str_p.replace('<b> ', '<b>')
            str_p = str_p.replace('</b>\n', '</b><br>\n')

            d.texto = str_p
            d.save()
            # print(str_p)

        return
        # abre autografo 1193, captura tabelas do anexo i e adiciona em seus
        # dispositivos
        html_file = open('/home/leandro/Downloads/702/aut.html', 'r').read()

        soup = bs(html_file, "html.parser")

        tables = list(soup.find_all("table"))

        # for t in tables:
        #    print(t)

        ds = Dispositivo.objects.filter(
            ta_id=9665,
            dispositivo_raiz_id=197223, id__gt=197229).order_by('ordem')

        ti = 0
        for d in ds:
            if d.texto and 'table' not in d.texto:
                continue

            t = tables[ti]
            ti += 1

            tag_b_prev = t.find_all_previous('b', {}, '', 1)

            texto = ''
            if len(tag_b_prev) == 1:
                texto = str(tag_b_prev[0].contents[0])
                texto = texto.replace('\n', ' ')
                texto = texto.replace('&nbsp;', ' ')
                texto = texto.replace(' – ', ' ')
                texto = texto.strip()
                texto = texto.split(' ')
                texto = ' '.join(texto[1:])
                print(texto)

            st = f'{texto}\n{t}<br>'

            d.texto = st
            d.save()

        return
        num_chaves = {}
        for u in UrlizeReferencia.objects.filter(url=''):
            p = UrlizeReferencia.urlize(u.chave, return_result_patterns=True)

            key = f'{p[0][10]}{p[0][12]}'

            if key not in num_chaves:
                num_chaves[key] = []

            num_chaves[key].append(u)

        num_chaves = list(num_chaves.items())

        num_chaves.sort(reverse=True, key=lambda i: len(i[1]))

        for item in num_chaves:
            for u in item[1]:
                print(u.chave, u.url)
                #u.url = 'https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm'
                # u.save()
            print('--------------------')
            print('--------------------')

            # for u in item[1]:
            ##    print(u.chave, u.url)
            #    u.url = 'https://legisla.casacivil.go.gov.br/pesquisa_legislacao/87672/lei-8268'
            #    u.save()
        return

        # list todos os orderings dos models

        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                if not m._meta.ordering:
                    print(m)

        return

        #

        """ocrmypdf.ocr(
            '/home/leandro/Downloads/processo_10252023.pdf',
            '/home/leandro/Downloads/processo_10252023_pdfa.pdf',
            language='por',
            force_ocr=True,
            # redo_ocr=True,
            # skip_text=True,
            jobs=4,
            output_type='pdfa-2',
            # image_dpi=72,
            # jpg_quality=60,
            # png_quality=30,
            optimize=3,
            # jbig2_lossy=True,
            # oversample=20,
            pdfa_image_compression="jpeg",
            plugins=[
                pathlib.Path(
                    '/home/leandro/desenvolvimento/envs/cmj/ocrmypdf_plugin.py')
            ]
        )"""

        in_file = '/home/leandro/Downloads/L4658.pdf'
        out_file = '/home/leandro/Downloads/L4658_out.pdf'

        os.makedirs('/home/leandro/TEMP/teste/rgb', exist_ok=True)
        os.makedirs('/home/leandro/TEMP/teste/gray', exist_ok=True)

        #in_file = '/home/leandro/TEMP/teste/teste_compact.pdf'
        #out_file = '/home/leandro/TEMP/teste/teste_compact2.pdf'

        doc = fitz.open(in_file)
        doc_out = fitz.open()

        __quality = 80

        for idx, p in enumerate(doc):
            images = p.get_images()

            for idxi, i in enumerate(images):

                try:
                    xref = i[0]
                    mask = i[1]

                    img = doc.extract_image(xref)
                    ibytes = img['image']
                    # print(len(img_bytes))

                    imgpix = fitz.Pixmap(ibytes)
                    color_path = f'/home/leandro/TEMP/teste/rgb/teste-{idx:0>4}-{idxi:0>3}.{img["ext"]}'
                    imgpix.save(color_path, output=img['ext'])

                    igray = fitz.Pixmap(fitz.csGRAY, imgpix)
                    gray_path = f'/home/leandro/TEMP/teste/gray/teste-{idx:0>4}-{idxi:0>3}.{img["ext"]}'
                    # , jpg_quality=50)
                    igray.save(
                        gray_path, output=img['ext'], jpg_quality=__quality)
                    # ,
                    #ibytes = igray.tobytes(output=img['ext'], jpg_quality=70)

                    impil = Image.open(gray_path)

                    draw = ImageDraw.Draw(impil)
                    w = img['width']
                    h = img['height']
                    draw.rectangle((0, 0, 50, h), fill="white")
                    draw.rectangle((w - 50, 0, w, h), fill="white")

                    draw.rectangle((0, h - 25, w, h), fill="white")
                    draw.rectangle((0, 0, w, 40), fill="white")

                    contrast = ImageEnhance.Contrast(impil)
                    impil = contrast.enhance(1.2)

                    #sharpness = ImageEnhance.Sharpness(impil)
                    #impil = sharpness.enhance(1.1)

                    #brightness = ImageEnhance.Brightness(impil)
                    #impil = brightness.enhance(1.1)
                    factor = impil.width / 620
                    (width, height) = (
                        int(impil.width / factor),
                        int(impil.height / factor)
                    )
                    im_resized = impil.resize(
                        (width, height), resample=Resampling.LANCZOS)

                    im_resized.save(gray_path, quality=__quality, dpi=(72, 72))
                    # return

                    #ibytes = impil.tobytes()
                    img_replace(p, xref, filename=gray_path)  # stream=ibytes)

                    #imag = np.frombuffer(img_bytes, dtype='uint8')
                    #imag = cv2.imdecode(imag, cv2.IMREAD_COLOR)
                    #sharpened = unsharp_mask(imag)
                    #imag = increase_brightness(sharpened, value=10)
                    #img_bytes = imag.tobytes()
                    # print(len(img_bytes))
                    #cv2.imwrite('image.jpg', img2, [int(cv2.imwrite_jpeg_quality), 100])

                except Exception as e:
                    pass

        doc_out.insert_pdf(doc,)  # to_page=10)

        doc_out.save(out_file, garbage=4, pretty=True,
                     deflate=True, deflate_images=True,
                     clean=True)

        # return

        ocrmypdf.ocr(
            '/home/leandro/Downloads/L4658_out.pdf',
            '/home/leandro/Downloads/L4658_pdfa.pdf',
            language='por',
            # force_ocr=True,
            # redo_ocr=True,
            skip_text=True,
            jobs=8,
            output_type='pdfa-2',
            image_dpi=72,
            jpg_quality=__quality,
            png_quality=__quality,
            optimize=3,
            jbig2_lossy=True,
            oversample=20,
            pdfa_image_compression="jpeg",
            plugins=[
                pathlib.Path(
                    '/home/leandro/desenvolvimento/envs/cmj/ocrmypdf_plugin.py')
            ]

        )

        return

        normas = NormaJuridica.objects.filter(
            numero__gte=1228,
            ano__gte=1987,
            numero__lte=1399,
            ano__lte=1990
        ).order_by('numero')

        ArqDoc.objects.all().delete()
        reset_id_model(ArqDoc)
        for n in normas:

            if not n.texto_integral:
                continue

            print(n)

            ad = ArqDoc()
            ad.codigo = n.numero
            ad.titulo = n.epigrafe
            ad.descricao = n.ementa
            ad.data = n.data
            ad.classe_estrutural_id = 1273

            ad.owner_id = 1
            ad.modifier_id = 1

            ad.save()

            path = n.texto_integral.original_path or n.texto_integral.path
            f = open(path, 'rb')
            f = File(f)
            ad.arquivo.save(path.split('/')[-1], f)
            ad.save()

        return

        # post_save.disconnect(dispatch_uid='timerefresh_post_signal')

        # m = MateriaLegislativa.objects.get(pk=19819)
        # m.texto_original.shorten_file_name()
        # self.criar_pdfs()

        self.pdftopdfa()
        return
        # print(text)

        #pdfFileObj = open(ff, 'rb')
        # try:
        #    pdfReader = PdfFileReader(pdfFileObj)
        #    pageObj = pdfReader.getPage(0)
        #    text = pageObj.extractText()
        # except:
        #    pdfReader = PdfFileReader(pdfFileObj, strict=False)
        #    pageObj = pdfReader.getPage(0)
        #    text = pageObj.extractText()

        #doc = fitz.open(ff)

        # for page in doc:
        #    t = page.get_text("words")
        #    text.append(t)
        #text = '\n'.join(text)

        materias = MateriaLegislativa.objects.filter(
            tipo_id=1, ano__gte=2020
        ).order_by('-ano', '-numero')

        for m in materias:
            ff = m.texto_original.path

            #pdf = pikepdf.Pdf.open(ff)
            #page1 = pdf.pages[0]

            text = extract_text(ff)
            text = text.split('\n')

            text = map(lambda t: t.strip(), text)
            text = map(lambda t: t.upper(), text)
            text = list(text)

            found = -1
            for i, t in enumerate(text):
                if t.startswith('PROJETO') or t.startswith('PROPOSTA'):
                    found = i
                    break

            if found == -1:
                print('padrão inicial não encontrado: ', m)
                continue
            text = ' '.join(text[i:])
            while '  ' in text:
                text = text.replace('  ', ' ')

            print(text[0:100])

            #rx = re.compile(r'(PROJETO|PROPOSTA)')

    def transformar_pdfs_em_imagens(self, *args, **options):
        folder_raiz = '/home/leandro/Downloads/leyse/'

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

    def criar_pdfs__simone(self, *args, **options):
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

    def get_all_tas(self):

        # get em todos textos articulados para gerar cache

        for norma in NormaJuridica.objects.all().order_by(
            '-norma_de_destaque',
            '-id'
        ):
            ta = norma.texto_articulado.all().first()
            if not ta:
                continue

            url = f'https://www.jatai.go.leg.br/ta/{ta.id}/text'

            try:
                res = requests.get(url)
                print(url, norma, res.status_code)
            except Exception as e:
                print(f"Erro: {e}")
                print(res.content)

        return
