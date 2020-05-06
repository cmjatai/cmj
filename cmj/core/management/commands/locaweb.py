

import logging

import boto3
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

    def run_upload_completo(self):
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY

        try:

            s3 = boto3.client(
                's3',
                # endpoint_url='https://object-storage.locaweb.com.br/',
                endpoint_url='https://lss.locawebcorp.com.br',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name='sa-east-1',
                # use_ssl=True
            )
        except:
            print('Erro na conexão com a locaweb')
            return

        print('--------- Locaweb ----------')
        reset = False

        bucket_name = 'cmjatai_teste'

        count = 0
        for app in apps.get_app_configs():
            print(app)
            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():

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

                for i in m.objects.all():
                    if not hasattr(i, 'metadata'):
                        print(i, 'não tem metadata')
                        continue

                    metadata = i.metadata
                    for fn in i.FIELDFILE_NAME:

                        ff = getattr(i, fn)
                        if not ff:
                            continue

                        if not metadata:
                            metadata = {}

                        if 'locaweb' not in metadata:
                            metadata['locaweb'] = {}

                        if fn not in metadata['locaweb']:
                            metadata['locaweb'][fn] = False

                        if reset:
                            metadata['locaweb'][fn] = False

                        if metadata['locaweb'][fn]:
                            continue

                        try:
                            s3.upload_file(
                                ff.path,
                                'cmjatai_teste',
                                ff.name,
                                ExtraArgs={'ACL': 'public-read',
                                           'Metadata': {'pk': f'{i._meta.label_lower}.{i.id}'}
                                           }
                            )
                        except Exception as e:
                            print(e)
                        else:
                            metadata['locaweb'][fn] = True
                            i.metadata = metadata
                            i.save()

                            count += 1

                            if count == 10:
                                return
