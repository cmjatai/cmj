
from datetime import datetime
import logging
import os
import subprocess
import sys

from django.apps import apps
from django.utils import timezone

from cmj.arq.models import DraftMidia
from cmj.celery import app
from sapl.utils import hash_sha512


logger = logging.getLogger(__name__)


@app.task(queue='celery', bind=True)
def task_ocrmypdf(self, app_label, model_name, field_name, pk, jobs, compact=False):
    task = task_ocrmypdf_compact_function if compact else task_ocrmypdf_function
    task(app_label, model_name, field_name, pk, jobs)


def console(cmd):
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)


def task_ocrmypdf_function(app_label, model_name, field_name, pk, jobs):
    print('task_ocrmypdf_function')
    model = apps.get_model(app_label, model_name)

    list_instances = model.objects.filter(id__in=pk)

    for instance in list_instances:
        f = getattr(instance, field_name).file

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

        r = console(' '.join(cmd))
        print(r[0])
        print(r[1].decode('utf-8'))
        print(r[2].decode('utf-8'))
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


def task_ocrmypdf_compact_function(app_label, model_name, field_name, pk, jobs):
    print('task_ocrmypdf_compact_function')

    model = apps.get_model(app_label, model_name)

    list_instances = model.objects.filter(id__in=pk)

    for instance in list_instances:
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

        r = console(' '.join(cmd))
        print(r[0])
        print(r[1].decode('utf-8'))
        print(r[2].decode('utf-8'))
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
