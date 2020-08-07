from datetime import datetime, timedelta
import logging
import os

import boto3
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from sapl.utils import hash_sha512


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    s3c = None
    s3r = None

    s3_server = 's3_cmj'

    bucket_name = 'cmjatai_portal'
    days_validate = 60

    start_time = None
    exec_time = 1800

    count_registros = 0

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        # self.close_files()

        # self.calcular_validacao()
        # return

        # self.distribuir_validacao()
        # return

        # self.count_registers(full=False)
        # return

        self.start_time = timezone.localtime()

        self.s3_server = 's3_cmj'
        self.s3_connect()
        self.s3_sync()

        if not settings.DEBUG:
            self.update_backup_postgresql()

        self.s3_server = 'locaweb'
        self.s3_connect()
        self.s3_sync()

        if not settings.DEBUG:
            self.update_backup_postgresql()

        print(timezone.localtime())
        print(self.count_registros)

        #self.s3_sync(only_reset=False, model_name='NormaJuridica')
        #self.s3_sync(app_label='sapl.norma', model_name='NormaJuridica')

        #obj = n = NormaJuridica.objects.get(pk=8727)
        #self.restore_file_from_object(self.bucket_name, obj)

    def s3_connect(self):

        if self.s3_server == 'locaweb':
            access_key = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
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

    def has_bucket(self, bucket_name):
        bs = self.s3r.buckets.all()
        for b in bs:
            if b.name == bucket_name:
                return True
        return False

    def list_bucket(self):
        bs = self.s3r.buckets.all()
        if settings.DEBUG:
            for b in bs:
                print(b.name)
        return bs

    def create_bucket(self, bucket_name):
        if self.has_bucket(bucket_name):
            return
        self.s3r.create_bucket(Bucket=bucket_name)

    def __clear_bucket(self, bucket_name):
        b = self.get_bucket(bucket_name)

        for o in b.objects.all():
            print(o)
            o.delete()

    def s3_sync(self, app_label=None, model_name=None, only_reset=False):

        print('--------- {} ----------'.format(self.s3_server))
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
                    dua = f
                    print(dua)
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        #print(m, 'auto_now deve ser desativado.')
                        # continue  # auto_now deve ser desativado
                        print(m, 'desativando auto_now')
                        dua.auto_now = False

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

                    model_exec = True

                if not model_exec:
                    continue
                print(m, m.objects.all().count())
                pre_save.disconnect(
                    sender=m,
                    dispatch_uid='cmj_pre_save_signed_{}_{}'.format(
                        app.name.replace('.', '_'),
                        m._meta.model_name
                    ))

                for i in m.objects.all().order_by('-id'):

                    if not hasattr(i, 'metadata'):
                        #print(i, 'não tem metadata')
                        continue
                    else:
                        if only_reset:
                            if i.metadata and \
                                    self.s3_server in i.metadata:
                                i.metadata[self.s3_server] = {}
                                i.save()
                                print(i)
                            continue

                    metadata = i.metadata if i.metadata else {}
                    for fn in i.FIELDFILE_NAME:

                        ff = getattr(i, fn)
                        if not ff:
                            continue
                        if not os.path.exists(ff.path):
                            print('Arquivo registrado mas não existe', i.id, i)
                            continue

                        # if hasattr(ff, 'original_path'):
                        #    self.checar_consistencia(i, ff, fn)
                        # continue

                        if not metadata:
                            metadata = {}

                        if self.s3_server not in metadata:
                            metadata[self.s3_server] = {}

                        if fn not in metadata[self.s3_server]:
                            metadata[self.s3_server][fn] = {
                                'path': None,
                                'original_path': None,
                                'validate': None,
                                'hash': None,
                                'original_hash': None

                            }

                        if reset:
                            metadata[self.s3_server][fn] = {
                                'path': None,
                                'original_path': None,
                                'validate': None,
                                'hash': None,
                                'original_hash': None
                            }

                        count_update = 0
                        try:
                            count_update += self.send_file(
                                metadata, i, ff, fn, 'path', 'hash')

                            count_update += self.send_file(
                                metadata, i, ff, fn,
                                'original_path', 'original_hash')

                        except Exception as e:
                            print(e)
                            print(count)
                            return
                        else:
                            if count_update:
                                i.metadata = metadata
                                i.save()
                                count += 1
                                print(count)
                            else:
                                self.count_registros += 1
                                try:
                                    validate = i.metadata[self.s3_server][fn]['validate']
                                    if validate:
                                        lt = timezone.localtime()
                                        validate = parse_datetime(validate)
                                        if (lt - validate).days >= self.days_validate:
                                            i.metadata[self.s3_server][
                                                fn]['validate'] = lt
                                            i.save()
                                except Exception as ee:
                                    print(ee, metadata)

                            if (count == 500 or
                                    timezone.localtime() -
                                    self.start_time >
                                    timedelta(seconds=self.exec_time)):
                                return

    def checar_consistencia(self, i, ff, fn):
        try:
            existe_path = os.path.exists(ff.path)
            existe_original_path = os.path.exists(ff.original_path)
            if not existe_path:
                print('ARQUIVO PATH NÃO ENCONTRADO:',
                      i.id, i, ff.name)
            if not existe_original_path:
                dir_name = os.path.dirname(ff.original_path)
                list_dir = os.listdir(dir_name)
                if len(list_dir) == 1:
                    file_name = os.path.basename(ff.path)
                    original_file_rename_old = '{}/{}'.format(
                        dir_name, list_dir[0])
                    original_file_rename_new = '{}/{}'.format(
                        dir_name, file_name)

                    os.rename(original_file_rename_old,
                              original_file_rename_new)
                else:
                    print('ARQUIVO ORIGINAL PATH NÃO ENCONTRADO:',
                          i.id, i, ff.name, len(ff.name))
        except Exception as e:
            print(i, e)

    def temp_file_from_object(self, bucket_name, obj, fn, attr_path):

        ff = getattr(obj, fn)
        if not ff:
            return None

        if not hasattr(ff, attr_path):
            return None

        b = self.get_locaweb_bucket(bucket_name)

        t_p = '/tmp/br.leg.go.jatai.portalcmj.{}.{}.{}.{}.{}'.format(
            attr_path,
            obj._meta.app_label,
            obj._meta.model_name,
            obj.id,
            fn
        )

        try:
            r_p = b.download_file(
                ff.name,
                t_p
            )

            return t_p

        except Exception as e:
            print(e)
            return False

    def validate_file(self, metadata, i, fn, attr_path, attr_hash):
        if metadata[self.s3_server][fn]['validate']:
            if isinstance(metadata[self.s3_server][fn]['validate'], str):
                v = parse_datetime(metadata[self.s3_server][fn]['validate'])
            else:
                v = metadata[self.s3_server][fn]['validate']

            # if timezone.localtime() - v > timedelta(seconds=30):
            #print(self.start_time - v)
            if self.start_time - v < timedelta(days=self.days_validate):
                return True

            t_p = self.temp_file_from_object(
                self.bucket_name,
                i,
                fn, attr_path
            )
            if t_p is None:
                return True
            if not t_p:
                return False

            hash = hash_sha512(t_p)

            if hash == metadata[self.s3_server][fn][attr_hash]:
                return True

        else:
            print('Documento Sem validação:', i.id, i)
        return False

    def send_file(self, metadata, i, ff, fn, attr_path, attr_hash):

        if not hasattr(ff, attr_path):
            return 0

        if os.path.exists(getattr(ff, attr_path)):

            if metadata[self.s3_server][fn][attr_path]:
                # return 0
                t = os.path.getmtime(getattr(ff, attr_path))
                date_file = datetime.fromtimestamp(t, timezone.utc)

                if parse_datetime(metadata[self.s3_server][fn][attr_path]) > date_file:
                    result = self.validate_file(
                        metadata, i, fn, attr_path, attr_hash)
                    if result:
                        return 0
            # return 0
            print('Enviando...', i, attr_path)

            """self.s3Lc.upload_file(
                getattr(ff, attr_path),
                self.bucket_name,
                ff.original_name if 'original' in attr_path else ff.name,
                ExtraArgs={
                    'ACL': 'private',
                    'Metadata': {
                        'pk': f'{i._meta.label_lower}.{i.id}'
                    }
                }
            )"""

            obj = self.s3r.Object(
                self.bucket_name,
                ff.original_name if 'original' in attr_path else ff.name,
            )
            with open(getattr(ff, attr_path), "rb") as f:
                obj.upload_fileobj(
                    f,
                    ExtraArgs={
                        'ACL': 'private',
                        'Metadata': {
                            'pk': f'{i._meta.label_lower}.{i.id}'
                        }
                    })

            metadata[self.s3_server][fn][attr_path] = timezone.localtime()
            metadata[self.s3_server][fn][attr_hash] = hash_sha512(
                getattr(ff, attr_path))
            metadata[self.s3_server][fn]['validate'] = timezone.localtime()

            return 1
        return 0

    def distribuir_validacao(self):
        # distribui base em days_validate
        count = 0
        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue
            print(app)

            for m in app.get_models():
                model_exec = False

                for f in m._meta.get_fields():
                    dua = f
                    print(dua)
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        #print(m, 'auto_now deve ser desativado.')
                        # continue  # auto_now deve ser desativado
                        print(m, 'desativando auto_now')
                        dua.auto_now = False

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

                    model_exec = True

                if not model_exec:
                    continue
                print(m)

                pre_save.disconnect(
                    sender=m,
                    dispatch_uid='cmj_pre_save_signed_{}_{}'.format(
                        app.name.replace('.', '_'),
                        m._meta.model_name
                    ))

                count_model = m.objects.count()

                if not count_model:
                    continue

                total_seconds = self.days_validate * 86400
                interval_seconds = timedelta(
                    seconds=total_seconds / count_model)

                td = timedelta(seconds=total_seconds)

                for i in m.objects.all().order_by('-id'):

                    if not hasattr(i, 'metadata'):
                        #print(i, 'não tem metadata')
                        continue

                    if not i.metadata:
                        continue

                    if self.s3_server not in i.metadata:
                        continue

                    #metadata = i.metadata if i.metadata else {}
                    for fn in i.FIELDFILE_NAME:

                        if fn not in i.metadata[self.s3_server]:
                            continue

                        if 'validate' not in i.metadata[self.s3_server][fn]:
                            continue

                        if not i.metadata[self.s3_server][fn]['validate']:
                            continue

                        i.metadata[self.s3_server][fn]['validate'] = timezone.localtime(
                        ) - td
                        i.save()

                    td -= interval_seconds

    def calcular_validacao(self):

        count = 0
        lt = timezone.localtime()

        calc = {}

        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue
            print(app)

            for m in app.get_models():
                model_exec = False

                for f in m._meta.get_fields():
                    dua = f
                    print(dua)
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        #print(m, 'auto_now deve ser desativado.')
                        # continue  # auto_now deve ser desativado
                        print(m, 'desativando auto_now')
                        dua.auto_now = False

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

                    model_exec = True

                if not model_exec:
                    continue
                print(m)

                pre_save.disconnect(
                    sender=m,
                    dispatch_uid='cmj_pre_save_signed_{}_{}'.format(
                        app.name.replace('.', '_'),
                        m._meta.model_name
                    ))

                for i in m.objects.all().order_by('-id'):
                    if not hasattr(i, 'metadata'):
                        continue
                    if not i.metadata:
                        continue
                    if self.s3_server not in i.metadata:
                        continue

                    md = i.metadata if i.metadata else {}
                    for fn in i.FIELDFILE_NAME:
                        if fn not in md[self.s3_server]:
                            continue
                        if 'validate' not in md[self.s3_server][fn]:
                            continue
                        if not md[self.s3_server][fn]['validate']:
                            continue
                        td = lt - \
                            parse_datetime(md[self.s3_server][fn]['validate'])
                        d = td.days if td.days > 0 else -1
                        if d not in calc:
                            calc[d] = 0

                        calc[d] += 1
        print(calc)

    def count_registers(self, full=True):

        print('--------- CountRegisters ----------')

        for app in apps.get_app_configs():
            for m in app.get_models():
                count = m.objects.all().count()
                if full or count > 1000:
                    print(count, m, app)

    def update_backup_postgresql(self):

        path_name = '{}BD_POSTGRESQL/'.format(settings.ABSOLUTE_PATH_BACKUP)

        list_dir = os.listdir(path_name)

        for item in list_dir:

            t = os.path.getmtime(f'{path_name}{item}')
            date_file = datetime.fromtimestamp(t, timezone.utc)

            obj = self.s3r.Object(
                'cmjatai_postgresql',
                f'{path_name}{item}'[1:]

            )

            send = True

            try:
                if date_file < obj.last_modified:
                    send = False
            except:
                pass

            if not send:
                continue

            print('Enviando...', path_name, item)
            with open(f'{path_name}{item}', "rb") as f:
                obj.upload_fileobj(
                    f,
                    ExtraArgs={
                        'ACL': 'private',
                    })

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
            except Exception as e:
                print(e)

            if hasattr(ff, 'original_path'):
                try:
                    b.download_file(
                        ff.original_name,
                        ff.original_path
                    )
                except Exception as e:
                    print(e)
