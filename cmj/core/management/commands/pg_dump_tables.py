from datetime import datetime, timedelta
import logging
import os
import subprocess
from time import sleep

import boto3
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from cmj.utils import Manutencao
from sapl.base.models import CasaLegislativa
from sapl.utils import hash_sha512


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()

        post_save.disconnect(dispatch_uid='timerefresh_post_signal')



        for app in apps.get_app_configs():
            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():

                table = m._meta.db_table
                cmd = ['/usr/bin/pg_dump --username "readonly" --host "10.3.163.254" ',
                       '--format=c --compress="9" -d cmj -t ',
                       table,
                       '--file="~/bd_cmj/' + table + '.backup"']

                try:
                    subprocess.run(' '.join(cmd), shell=True)
                except Exception as e:
                    print(m, e)
