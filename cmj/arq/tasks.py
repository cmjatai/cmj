
from datetime import datetime
import logging
import os
import subprocess
import sys

from django.apps import apps
from django.utils import timezone
import fitz

from cmj.arq.models import DraftMidia
from cmj.celery import app
from sapl.utils import hash_sha512


logger = logging.getLogger(__name__)


def console(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)


def task_ocrmypdf_function(app_label, model_name, field_name, id_list, jobs):
    print(f'task_ocrmypdf_function {app_label} {model_name} {field_name} {id_list} {jobs}')
    logger.info(f'task_ocrmypdf_function {app_label} {model_name} {field_name} {id_list} {jobs}')

    model = apps.get_model(app_label, model_name)

    for id_item in id_list:
        try:
            instance = model.objects.get(pk=id_item)
            if instance.metadata['ocrmypdf']['pdfa'] != DraftMidia.METADATA_PDFA_AGND:
                continue
        except:
            continue

        f = getattr(instance, field_name).file
        
        try:
            d_new = fitz.open()
            doc = fitz.open(f)
            d_new.insert_pdf(doc, from_page = 0, to_page = len(doc))
            doc.close()

            d_new.metadata['title'] = doc.metadata['title']
            d_new.metadata['producer'] = 'PortalCMJ'
            d_new.set_metadata(d_new.metadata)

            fn = f'{f}.tmp'
            d_new.save(fn, garbage = 3, clean = True, deflate = True)
        except:
            pass
        else:
            fpath = f.name
            os.remove(fpath)
            os.rename(fn, fpath)

        cmd = ["{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
               #"-q",                  # Execução silenciosa
               "-l por",              # tesseract portugues
               f'-j {jobs}',     # duas threads
               #"--fast-web-view 10000000",   # não inclui fast web view
               #"--image-dpi 300",
               #"--rotate-pages",
               #"--rotate-pages-threshold 1",
               #"--remove-background",
               "--force-ocr",
               #"--optimize 0",
               #"--jpeg-quality 100",
               #"--png-quality 100",
               #"--jbig2-lossy",
               "--invalidate-digital-signatures",
               #"--deskew",
               #"--clean-final",
               #"--pdfa-image-compression jpeg",  # jpeg  lossless
               "--output-type pdfa-2",
               #"--tesseract-timeout 0",
               f'"{f}"',
               f'"{f}"']

        print(' '.join(cmd))
        logger.info(' '.join(cmd))

        md = instance.metadata or {}
        md.update({
            'ocrmypdf': {
                'pdfa': DraftMidia.METADATA_PDFA_PROC,
            }
        })

        instance.save()

        r = console(' '.join(cmd))

        #logger.info(r[0])
        #logger.info(r[1].decode('utf-8'))

        print(r[2].decode('utf-8'))
        logger.info(r[2].decode('utf-8'))


        if not r[0]:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_PDFA,
                    'hash_code': hash_sha512(f),
                    'lastmodified': datetime.fromtimestamp(os.path.getmtime(f.file.name)),
                    'size': os.path.getsize(f.file.name)
                }
            })
        else:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_NONE,
                }
            })

        instance.save()


@app.task(queue='cq_arq', bind=True)
def task_ocrmypdf(self, app_label, model_name, field_name, id_list, jobs, compact=False):
    print(f'task_ocrmypdf {app_label} {model_name} {field_name} {id_list} {jobs}')
    logger.info(f'task_ocrmypdf {app_label} {model_name} {field_name} {id_list} {jobs}')

    task = task_ocrmypdf_compact_function if compact else task_ocrmypdf_function
    task(app_label, model_name, field_name, id_list, jobs)


def task_ocrmypdf_compact_function(app_label, model_name, field_name, id_list, jobs):
    print(f'task_ocrmypdf_compact_function {app_label} {model_name} {field_name} {id_list} {jobs}')
    logger.info(f'task_ocrmypdf_compact_function {app_label} {model_name} {field_name} {id_list} {jobs}')

    model = apps.get_model(app_label, model_name)

    for id_item in id_list:
        instance = model.objects.get(pk=id_item)
        try:
            if instance.metadata['ocrmypdf']['pdfa'] != DraftMidia.METADATA_PDFA_AGND:
                continue
        except:
            continue

        f = getattr(instance, field_name).file

        cmd = ["{}/ocrmypdf".format('/'.join(sys.executable.split('/')[:-1])),
               #"-q",                  # Execução silenciosa
               "-l por",              # tesseract portugues
               f'-j {jobs}',     # duas threads
               #"--fast-web-view 10000000",   # não inclui fast web view
               "--image-dpi 72",
               #"--rotate-pages",
               #"--rotate-pages-threshold 1",
               #"--remove-background",
               "--skip-text",
               "--optimize 3",
               "--jpeg-quality 60",
               "--png-quality 60",
               #"--jbig2-lossy",
               #"--invalidate-digital-signatures",
               #"--deskew",
               #"--clean-final",
               #"--pdfa-image-compression jpeg",  # jpeg  lossless
               "--output-type pdfa-2",
               #"--tesseract-timeout 0",
               f'"{f}"',
               f'"{f}"']

        print(' '.join(cmd))
        logger.info(' '.join(cmd))

        r = console(' '.join(cmd))
        #logger.info(r[0])
        #logger.info(r[1].decode('utf-8'))

        print(r[2].decode('utf-8'))
        logger.info(r[2].decode('utf-8'))

        md = instance.metadata or {}

        if not r[0]:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_PDFA,
                    'hash_code': hash_sha512(f),
                    'lastmodified': datetime.fromtimestamp(os.path.getmtime(f.file.name)),
                    'size': os.path.getsize(f.file.name)
                }
            })
        else:
            md.update({
                'ocrmypdf': {
                    'pdfa': DraftMidia.METADATA_PDFA_NONE,
                }
            })

        instance.save()
