
from datetime import datetime
import logging
import os

import boto3
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sapl.norma.models import NormaJuridica


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    s3c = None
    s3r = None

    bucket_name = 'cmjatai_portal'

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.s3_connect()
        # self.__clear_bucket('cmjatai_teste')
        self.s3_sync(app_label='sapl.norma', model_name='NormaJuridica')

    def download_file_from_object(self, bucket_name, obj):
        b = self.get_bucket(bucket_name)
        obj = n = NormaJuridica.objects.get(pk=8711)

        for fn in obj.FIELDFILE_NAME:

            ff = getattr(obj, fn)
            if not ff:
                continue
            try:
                b.download_file(
                    ff.name, '/home/leandro/TEMP/teste_download_8711.pdf')
            except Exception as e:
                print(e)

            try:
                b.download_file(
                    ff.original_name, '/home/leandro/TEMP/{}'.format(ff.original_name))
            except Exception as e:
                print(e)

    def __clear_bucket(self, bucket_name):
        b = self.get_bucket(bucket_name)

        for o in b.objects.all():
            print(o)
            o.delete()

    def has_bucket(self, bucket_name):
        bs = self.s3r.buckets.all()
        for b in bs:
            if b.name == bucket_name:
                return True
        return False

    def get_bucket(self, bucket_name):
        bs = self.s3r.buckets.all()
        for b in bs:
            if b.name == bucket_name:
                return b
        raise Exception('Bucket não existe!')

    def s3_connect(self):

        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        try:
            self.s3c = boto3.client(
                's3',
                endpoint_url='https://lss.locawebcorp.com.br',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='sa-east-1')
            self.s3r = boto3.resource(
                's3',
                endpoint_url='https://lss.locawebcorp.com.br',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='sa-east-1')
        except:
            print('Erro na conexão com a locaweb')

    def s3_sync(self, app_label=None, model_name=None):

        print('--------- Locaweb ----------')
        reset = False

        count = 0
        for app in apps.get_app_configs():
            if app_label and app.name != app_label:
                print(app.name)
                continue

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue
            print(app)

            for m in app.get_models():
                model_exec = False

                if model_name and m._meta.object_name != model_name:
                    continue

                for f in m._meta.get_fields():
                    if not isinstance(f, FileField):
                        continue

                    # se possui FileField, o model então
                    # deve possuir FIELDFILE_NAME
                    assert hasattr(m, 'FIELDFILE_NAME'), '{} não possui FIELDFILE_NAME'.format(
                        m._meta.label)

                    # se possui FileField, o model então
                    # deve possuir metadata
                    assert hasattr(m, 'metadata'), '{} não possui metadata'.format(
                        m._meta.label)

                    # o campo field deve estar em FIELDFILE_NAME
                    assert f.name in m.FIELDFILE_NAME, '{} não está no FIELDFILE_NAME de {}'.format(
                        f.name,
                        m._meta.label)

                    dua = f
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        #print(m, 'auto_now deve ser desativado.')
                        # continue  # auto_now deve ser desativado
                        print(m, 'desativando auto_now')
                        dua.auto_now = False
                    model_exec = True

                if not model_exec:
                    continue
                print(m)
                for i in m.objects.all().order_by('-id'):

                    if not hasattr(i, 'metadata'):
                        #print(i, 'não tem metadata')
                        continue
                    # else:
                    #    if i.metadata and \
                    # 'locaweb' in i.metadata:
                    #        i.metadata['locaweb'] = {}
                    #        i.save()
                    #        print(i)
                    #    continue

                    metadata = i.metadata if i.metadata else {}
                    for fn in i.FIELDFILE_NAME:

                        ff = getattr(i, fn)
                        if not ff:
                            continue

                        self.checar_consistencia(i, ff, fn)
                        continue

                        if not metadata:
                            metadata = {}

                        if 'locaweb' not in metadata:
                            metadata['locaweb'] = {}

                        if fn not in metadata['locaweb']:
                            metadata['locaweb'][fn] = {
                                'path': None,
                                'original_path': None
                            }

                        if reset:
                            metadata['locaweb'][fn] = {
                                'path': None,
                                'original_path': None
                            }

                        count_update = 0
                        try:
                            count_update += self.send_file(
                                metadata, i, ff, fn, 'path')

                            count_update += self.send_file(
                                metadata, i, ff, fn, 'original_path')

                        except Exception as e:
                            print(e)
                        else:
                            if count_update:
                                i.metadata = metadata
                                i.save()
                                count += 1

                            if count == 100:
                                return

    def checar_consistencia(self, i, ff, fn):
        existe_path = os.path.exists(ff.path)
        existe_original_path = os.path.exists(ff.original_path)
        if not existe_path:
            print('ARQUIVO PATH NÃO ENCONTRADO:',
                  i.id, i, ff.name)
        if not existe_original_path:
            print('ARQUIVO ORIGINAL PATH NÃO ENCONTRADO:',
                  i.id, i, ff.name)

    def send_file(self, metadata, i, ff, fn, attr):
        if os.path.exists(getattr(ff, attr)):

            if metadata['locaweb'][fn][attr]:
                t = os.path.getmtime(getattr(ff, attr))
                date_file = datetime.fromtimestamp(
                    t, timezone.utc)

                if parse_datetime(metadata['locaweb'][fn][attr]) > date_file:
                    return 0

            self.s3c.upload_file(
                getattr(ff, attr),
                self.bucket_name,
                ff.original_name if 'original' in attr else ff.name,
                ExtraArgs={
                    'ACL': 'private',
                    'Metadata': {
                        'pk': f'{i._meta.label_lower}.{i.id}'
                    }
                }
            )

            metadata['locaweb'][fn][attr] = timezone.localtime()
            return 1
        return 0
