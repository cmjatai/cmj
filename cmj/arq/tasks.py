
from datetime import datetime
import logging
import os
import subprocess
import sys

from django.apps import apps
from django.utils import timezone

from cmj.celery import app
from sapl.utils import hash_sha512


logger = logging.getLogger(__name__)


@app.task(queue='celery', bind=True)
def task_ocrmypdf(self, app_label, model_name, field_name, pk):
    print('task_ocrmypdf')
    task_ocrmypdf_function(app_label, model_name, field_name, pk)


def console(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)


def task_ocrmypdf_function(app_label, model_name, field_name, pk):
    model = apps.get_model(app_label, model_name)

    instance = model.objects.get(pk=pk)

    f = getattr(instance, field_name).file

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
           f'"{f}"']

    print(' '.join(cmd))

    r = console(' '.join(cmd))

    md = instance.metadata or {}

    if not r[0]:
        md.update({
            'ocrmypdf': {
                'pdfa': True,
                'hash_code': hash_sha512(f),
                'lastmodified': datetime.fromtimestamp(os.path.getmtime(f.file.name)),
                'size': os.path.getsize(f.file.name)
            }
        })
    else:
        md.update({
            'ocrmypdf': {
                'pdfa': False,
            }
        })
    instance.save()
