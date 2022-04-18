from datetime import datetime, timedelta
import logging
import os
from time import sleep

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.dateparse import parse_datetime

import boto3
from cmj.signals import Manutencao
from sapl.norma.models import NormaJuridica
from sapl.utils import hash_sha512


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    s3c = None
    s3r = None

    s3_server = 's3_cmj'

    bucket_name = 'cmjatai_portal'

    def add_arguments(self, parser):
        parser.add_argument('--last_days',  type=int, default=0)
        parser.add_argument('--model', type=str, default='')
        parser.add_argument('--s3_server', type=str, default='s3_cmj')

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.s3_server = options['s3_server']
        self.last_days = options['last_days']
        self.model = options['model']

        self.s3_connect()
        self.s3_restore()

    def s3_connect(self):

        if self.s3_server == 'locaweb':
            access_key = settings.LOCAWEB_ACCESS_KEY_ID
            secret_key = settings.LOCAWEB_SECRET_ACCESS_KEY
            endpoint_url = 'https://lss.locawebcorp.com.br'
        elif self.s3_server == 's3_cmj':
            access_key = settings.S3_CMJ_ACCESS_KEY_ID
            secret_key = settings.S3_CMJ_SECRET_ACCESS_KEY
            endpoint_url = settings.S3_CMJ_ENDPOINT_URL

        try:
            self.s3c = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='sa-east-1')
            self.s3r = boto3.resource(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='sa-east-1')
        except:
            print('Erro na conexão com a s3 server', self.s3_server)

    def get_bucket(self, bucket_name):
        bs = self.s3r.buckets.all()
        for b in bs:
            if b.name == bucket_name:
                return b
        raise Exception('Bucket não existe!')

    def restore_file_from_object(self, bucket_name, obj):
        b = self.get_bucket(bucket_name)

        for fn in obj.FIELDFILE_NAME:

            ff = getattr(obj, fn)
            if not ff:
                continue

            directory = os.path.dirname(ff.path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            if hasattr(ff, 'original_path'):
                directory = os.path.dirname(ff.original_path)
                if not os.path.exists(directory):
                    os.makedirs(directory)

            try:
                b.download_file(
                    ff.name,
                    ff.path
                )
                print(obj, fn, ff.path, ff.name)
            except Exception as e:
                print(e)

            if hasattr(ff, 'original_path'):
                try:
                    b.download_file(
                        ff.original_name,
                        ff.original_path
                    )
                    print(obj, fn, ff.original_path, ff.original_name)
                except Exception as e:
                    print(e)

    def s3_restore(self):

        data_limite = None
        if self.last_days:
            data_limite = timezone.localtime() - timedelta(days=self.last_days)

        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():

                if self.model and self.model != m._meta.label:
                    continue

                if not hasattr(m, 'FIELDFILE_NAME'):
                    continue

                q = Q()
                if data_limite:
                    for fn in m.FIELDFILE_NAME:
                        q |= Q(
                            **{f'metadata__{self.s3_server}__{fn}__path__gte': data_limite})
                        q |= Q(
                            **{f'metadata__{self.s3_server}__{fn}__original_path__gte': data_limite})

                items = m.objects.filter(q).order_by('-id')

                for i in items:
                    self.restore_file_from_object(self.bucket_name, i)
