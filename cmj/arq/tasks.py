
from datetime import datetime
import logging
import os
import subprocess
import sys

from django.apps import apps
from django.utils import timezone
import fitz

from pymupdf import Point, Rect

from cmj.arq.models import DraftMidia
from cmj.celery import app
from sapl.utils import hash_sha512

import cv2
from PIL import Image

logger = logging.getLogger(__name__)


def console(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)


class PDFAltaCompactacao:
    def __init__(self, file_path, jobs):
        self.file_path = file_path
        self.jobs = jobs
        self.file_path_temp = f'{file_path}.tmp'
        self.doc = fitz.open(file_path)

        self.folder = os.path.dirname(file_path)
        self.filename = os.path.basename(file_path)
        self.filename_noext = os.path.splitext(self.filename)[0]

    def compactar(self):
        try:
            self.extrair_imagens()
            self.converter_imagens_para_pb()

            self.montar_pdf_grande()
            self.executar_ocrmypdf(
                "--force-ocr",
                f"-j {self.jobs}",
                self.file_path_temp,
                self.file_path_temp
            )

            self.substituir_imagens()
            self.executar_ocrmypdf(
                "--skip-text",
                #"--tesseract-timeout 0",
                f"-j {self.jobs}",
                f'{self.file_path_temp}2',
                f'{self.file_path_temp}2'
                )
        except Exception as e:
            raise Exception(e)
        else:
            os.remove(self.file_path)
            os.remove(f'{self.file_path_temp}')
            os.rename(f'{self.file_path_temp}2', self.file_path)

    def extrair_imagens(self):
        # converte todas as páginas do pdf para png em images
        self.images_names = []
        self.images = f'{self.folder}/images/{self.filename_noext}'
        os.makedirs(self.images, exist_ok=True)

        for i in range(len(self.doc)):
            page = self.doc[i]
            img_name = f'{i:0>6}.png'
            self.images_names.append(img_name)
            pix = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY)
            pix.save(f'{self.images}/{img_name}')

    def converter_imagens_para_pb(self):
        #cria copia de images em pb_images aplicando brilho e contraste e convertendo para '1'
        self.pb_images = f'{self.folder}/pb_images/{self.filename_noext}'
        os.makedirs(self.pb_images, exist_ok=True)

        for img_name in self.images_names:
            img = cv2.imread(f'{self.images}/{img_name}', cv2.IMREAD_GRAYSCALE)
            img = cv2.convertScaleAbs(img, alpha=1.4, beta=0)
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            cv2.imwrite(f'{self.pb_images}/{img_name}', img)

            img = Image.open(f'{self.pb_images}/{img_name}')
            img.compression_quality = 75
            img = img.convert('1')
            img.save(f'{self.pb_images}/{img_name}')

    def montar_pdf_grande(self):
        #monta um pdf grande com todas as páginas
        self.doc = fitz.open()
        for img_name in self.images_names:
            img = fitz.open(f'{self.images}/{img_name}')
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            img = fitz.open("pdf", pdfbytes)

            self.doc.insert_pdf(img, from_page=0, to_page=len(img))

            if False:
                w = 595
                h = 842
                if rect.width > rect.height:
                    h = w
                    w = 842
                rect = Rect(0, 0, w, h)
                page = self.doc.new_page(width=w, height=h)
                page.insert_image(rect, filename=f'{self.images}/{img_name}')

        self.doc.save(self.file_path_temp)
        self.doc.close()

    def executar_ocrmypdf(self, *args):
        #gera o pdf
        cmd = [
            "{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
            "-l por",
            "--optimize 3",
            "--output-type pdfa-2",
            "--invalidate-digital-signatures",
            "--jpeg-quality 50",
            "--png-quality 50",
            "--jbig2-lossy",
            "--pdfa-image-compression jpeg",
        ] + list(args)
        r = console(' '.join(cmd))

    def substituir_imagens(self):
        #substitui as imagens do pdf grande pelas imagens compactadas
        doc = fitz.open(self.file_path_temp)
        for i, img_name in enumerate(self.images_names):
            page = doc[i]
            xref = page.get_image_info(xrefs=True)[0]['xref']
            page.delete_image(xref)
            page.replace_image(xref=xref, filename=f'{self.pb_images}/{img_name}')
        doc.save(f'{self.file_path_temp}2')
        doc.close()


def task_ocrmypdf_function(app_label, model_name, field_name, id_list, jobs, task_name):
    #print(f'task_ocrmypdf_function {app_label} {model_name} {field_name} {id_list} {jobs} {task_name}')
    logger.info(f'task_ocrmypdf_function {app_label} {model_name} {field_name} {id_list} {jobs} {task_name}')

    model = apps.get_model(app_label, model_name)

    for id_item in id_list:
        try:
            instance = model.objects.get(pk=id_item)
            if instance.metadata['ocrmypdf']['pdfa'] != DraftMidia.METADATA_PDFA_AGND:
                continue
        except:
            continue

        f = getattr(instance, field_name).file

        md = instance.metadata or {}
        md.update({
            'ocrmypdf': {
                'pdfa': DraftMidia.METADATA_PDFA_PROC,
            }
        })

        instance.save()

        if task_name not in ('pdf2pdfa_rapida', 'pdf2pdfa_compacta'):
            try:
                d_new = fitz.open()
                doc = fitz.open(f)

                if task_name == 'pdf2pdfa_forcada':
                    for i in range(len(doc)):
                        page = doc[i]
                        pix = page.get_pixmap(dpi=300)
                        pixbytes= pix.tobytes()

                        w = 595
                        h = 842
                        if pix.width > pix.height:
                            h = w
                            w = 842

                        rect = Rect(0, 0, w, h)
                        page = d_new.new_page(width=w,  height=h)
                        page.insert_image(rect, stream=pixbytes)
                else:
                    d_new.insert_pdf(doc, from_page = 0, to_page = len(doc))
                    doc.close()

                d_new.metadata['title'] = doc.metadata['title']
                d_new.metadata['producer'] = 'PortalCMJ'
                d_new.set_metadata(d_new.metadata)

                fn = f'{f}.tmp'
                d_new.save(fn, garbage = 3, clean = True, deflate = True)
            except Exception as e:
                pass
            else:
                fpath = f.name
                os.remove(fpath)
                os.rename(fn, fpath)

        def cmj_ocrmypdf(*args):
            return [
                "{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
                #"-q",
                "-l por",
                f'-j {jobs}',
                "--optimize 3",
                "--output-type pdfa-2",
                "--invalidate-digital-signatures",
            ] + list(args) + [f'"{f}"', f'"{f}"']

        error_compact = False
        r = (0, b'', b'')
        cmd = []
        if task_name == 'pdf2pdfa_rapida':
            cmd = cmj_ocrmypdf(
                "--skip-text",
                "--tesseract-timeout 0",
            )
        elif task_name == 'pdf2pdfa_basica':
            cmd = cmj_ocrmypdf('--skip-text')
        elif task_name == 'pdf2pdfa_forcada':
            cmd = cmj_ocrmypdf('--force-ocr')
        elif task_name == 'pdf2pdfa_compacta':

            try:
                ce = PDFAltaCompactacao(f.name, jobs)
                ce.compactar()
            except Exception as e:
                error_compact = True
            else:
                error_compact = False

        if cmd:
            logger.info(' '.join(cmd))
            r = console(' '.join(cmd))
            logger.info(r[2].decode('utf-8'))

        if r[0] or error_compact:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_NONE,
                }
            })
        else:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_PDFA,
                    'hash_code': hash_sha512(f),
                    'lastmodified': datetime.fromtimestamp(os.path.getmtime(f.file.name)),
                    'size': os.path.getsize(f.file.name)
                }
            })

        instance.save()


@app.task(queue='cq_arq', bind=True)
def task_ocrmypdf(self, app_label, model_name, field_name, id_list, jobs, task_name):
    #f'task_ocrmypdf {app_label} {model_name} {field_name} {id_list} {jobs}')
    logger.info(f'task_ocrmypdf {app_label} {model_name} {field_name} {id_list} {jobs}')

    task_ocrmypdf_function(app_label, model_name, field_name, id_list, jobs, task_name)
