from datetime import datetime, timedelta
import logging
import os
from time import sleep

import boto3
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.fields.files import FileField
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from cmj.arq.models import DraftMidia
from cmj.utils import Manutencao
from sapl.utils import hash_sha512


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    s3c = None
    s3r = None

    s3_server = 's3_cmj'
    s3_full = ''

    bucket_name = 'cmjatai-portal'
    days_validate = 360

    start_time = None
    exec_time = 1800

    count_registros = 0

    def add_arguments(self, parser):
        parser.add_argument('--s3_server', type=str, default='')
        parser.add_argument('--s3_full', type=str, default='')

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        m.desativa_signals()

        # post_save.disconnect(dispatch_uid='timerefresh_post_signal')

        self.logger = logging.getLogger(__name__)

        # self.manutencao_buckets()
        # return

        self.s3_server = options['s3_server']
        self.s3_full = options['s3_full']

        init = datetime.now()

        s3_servers = ('s3_aws', 's3_cmj')
        s3_server = s3_servers[init.hour % 2]

        if self.s3_server:
            s3_server = self.s3_server

        print('--------- Iniciando:', s3_server)
        self.s3_server = s3_server

        self.s3_connect()

        if not settings.DEBUG:
            print('--------- Atualizando backup do BD ----------')
            self.update_backup_postgresql()

        self.start_time = timezone.localtime()

        try:

            self.s3_sync(count_exec=500)
            self.s3_size()

        except Exception as e:
            print('erro na sincronização:', e)

        print('Encerrando conexão com ', self.s3_server)
        sleep(5)
        self.s3c = None
        self.s3r = None
        sleep(5)

        print('Concluído...')

    def s3_connect(self):

        endpoint_url = ''
        if self.s3_server == 's3_aws':
            access_key = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
        elif self.s3_server == 's3_cmj':
            access_key = settings.S3_CMJ_ACCESS_KEY_ID
            secret_key = settings.S3_CMJ_SECRET_ACCESS_KEY
            endpoint_url = settings.S3_CMJ_ENDPOINT_URL

        try:
            if not endpoint_url:
                self.s3c = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name='sa-east-1')
                self.s3r = boto3.resource(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name='sa-east-1')
            else:
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

    def s3_sync(self, app_label=None, model_name=None, only_reset=False, count_exec=100):
        print('--------- S3 Sync ---------')

        reset = False

        for app in apps.get_app_configs():
            if app_label and app.name != app_label:
                # print(app.name)
                continue

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue
            # print(app)

            model_not_backup = (DraftMidia, )

            for m in app.get_models():
                model_exec = False

                if m in model_not_backup:
                    continue

                if model_name and m._meta.object_name != model_name:
                    continue

                for f in m._meta.get_fields():
                    dua = f
                    # print(dua)
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
                #print(m, m.objects.all().count())
                # pre_save.disconnect(
                #    sender=m,
                #    dispatch_uid='cmj_pre_save_signed_{}_{}'.format(
                #        app.name.replace('.', '_'),
                #        m._meta.model_name
                #    ))

                print(m)
                for i in m.objects.all().order_by('-id'):  #
                    #print(i.id, i)

                    if not hasattr(i, 'metadata'):
                        #print(i, 'não tem metadata')
                        continue
                    else:
                        if only_reset:
                            if i.metadata and \
                                    self.s3_server in i.metadata:

                                i.metadata[self.s3_server] = {}
                                i.save()
                                # print(i)
                            continue

                    if i.metadata and 'locaweb' in i.metadata:
                        del i.metadata['locaweb']

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

                        try:
                            ff.shorten_file_name()
                        except:
                            pass

                        if not metadata:
                            metadata = {}

                        if self.s3_server not in metadata:
                            metadata[self.s3_server] = {}

                        if fn not in metadata[self.s3_server]:
                            metadata[self.s3_server][fn] = {
                                # path, original_path Data de upload, arquivo com data no file
                                # system maior que esta data devem ser subidos
                                # novamente
                                'path': None,
                                'original_path': None,
                                'validate': None,  # ultima validação com o s3 em execução
                                'hash': None,
                                'original_hash': None,
                                'size': 0,
                                'original_size': 0

                            }

                        if reset:
                            metadata[self.s3_server][fn] = {
                                'path': None,
                                'original_path': None,
                                'validate': None,
                                'hash': None,
                                'original_hash': None,
                                'size': 0,
                                'original_size': 0
                            }

                        try:

                            td = parse_datetime(
                                metadata[self.s3_server][fn]['validate']
                            ) - parse_datetime(
                                metadata[self.s3_server][fn][
                                    'original_path' if metadata[self.s3_server][fn]['original_path'] else 'path'
                                ]
                            )

                            dv = (td.days / 180.0) * 60.0

                            self.days_validate = min(max(dv, 60), 365)
                        except:
                            self.days_validate = 60

                        count_update = 0
                        try:

                            count_update += self.send_file(
                                metadata, i, ff, fn, 'path', 'hash', 'size')

                            count_update += self.send_file(
                                metadata, i, ff, fn,
                                'original_path', 'original_hash', 'original_size')

                        except Exception as e:
                            print(e)
                            print(self.count_registros)
                            return
                        else:
                            if count_update:
                                i.metadata = metadata
                                i.save()
                                self.count_registros += 1
                                # print(count)
                            else:
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

                            if not self.s3_full:
                                if (self.count_registros == count_exec or
                                        timezone.localtime() -
                                        self.start_time >
                                        timedelta(seconds=self.exec_time)):
                                    print(
                                        '--------- {} ---------- INICIADO EM: {}'.format(self.s3_server, self.start_time))
                                    print(
                                        '--------- {} ---------- ENCERRADO EM: {}'.format(self.s3_server, timezone.localtime()))

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

        b = self.get_bucket(bucket_name)

        t_p = '/tmp/br.leg.go.jatai.portalcmj.{}.{}.{}.{}.{}'.format(
            attr_path,
            obj._meta.app_label,
            obj._meta.model_name,
            obj.id,
            fn
        )

        try:
            r_p = b.download_file(
                ff.original_name if 'original' in attr_path else ff.name,
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

            if self.s3_server == 's3_aws':
                # TODO: formular estratégia de validação periódica para AWS.
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

            if os.path.exists(t_p):
                os.remove(t_p)

            if hash == metadata[self.s3_server][fn][attr_hash]:
                return True

        else:
            self.logger.warn(
                'Documento Sem validação: {} - {}'.format(i.id, i))
            print('Documento Sem validação:', i.id, i)
        return False

    def send_file(self, metadata, i, ff, fn, attr_path, attr_hash, attr_size):

        if not hasattr(ff, attr_path):
            return 0

        if os.path.exists(getattr(ff, attr_path)):

            if not self.s3_full:
                if metadata[self.s3_server][fn][attr_path]:
                    # return 0
                    t = os.path.getmtime(getattr(ff, attr_path))
                    date_file = datetime.fromtimestamp(t, timezone.utc)

                    if parse_datetime(metadata[self.s3_server][fn][attr_path]) > date_file:
                        result = self.validate_file(
                            metadata, i, fn, attr_path, attr_hash)
                        if result:
                            return 0
                    else:
                        print(
                            f'Arquivo foi substituído, reenviando para o S3 {self.s3_server}...', i, attr_path)

            obj = self.s3r.Object(
                self.bucket_name,
                ff.original_name if 'original' in attr_path else ff.name,
            )

            if self.s3_full == 'only_new':
                try:
                    meta = obj.metadata
                    pk = meta['Pk' if 'Pk' in meta else 'pk']

                    if pk == f'{i._meta.label_lower}.{i.id}':
                        return 0

                except:
                    pass

            print(self.count_registros, 'Enviando...', i.id, i, attr_path)

            with open(getattr(ff, attr_path), "rb") as f:
                obj.upload_fileobj(
                    f,
                    ExtraArgs={
                        'ACL': 'private',
                        'Metadata': {
                            'pk': f'{i._meta.label_lower}.{i.id}'
                        },
                        'StorageClass': 'DEEP_ARCHIVE'  # 'INTELLIGENT_TIERING'

                    })

            if not self.s3_full or metadata[self.s3_server][fn][attr_hash] is None:
                metadata[self.s3_server][fn][attr_path] = timezone.localtime()
                metadata[self.s3_server][fn][attr_hash] = hash_sha512(
                    getattr(ff, attr_path))
                metadata[self.s3_server][fn]['validate'] = timezone.localtime()

                metadata[self.s3_server][fn][attr_size] = os.path.getsize(
                    getattr(ff, attr_path))

            return 1
        return 0

    def update_backup_postgresql(self):

        path_name = '{}BD_POSTGRESQL/'.format(settings.ABSOLUTE_PATH_BACKUP)

        list_dir = os.listdir(path_name)

        for item in list_dir:

            t = os.path.getmtime(f'{path_name}{item}')
            date_file = datetime.fromtimestamp(t, timezone.utc)

            obj = self.s3r.Object(
                'cmjatai-postgresql',
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
            try:
                with open(f'{path_name}{item}', "rb") as f:
                    obj.upload_fileobj(
                        f,
                        ExtraArgs={
                            'ACL': 'private',
                        })
            except Exception as e:
                print(e)
                self.logger.error(item, str(e))

            sleep(5)

    def restore_file_from_bucket(self, bucket_name):
        b = self.get_bucket(bucket_name)

        for o in b.objects.all():

            if not o.key.endswith('.backup'):
                continue

            opath = f'/tmp/{o.key}'

            directory = os.path.dirname(opath)
            if not os.path.exists(directory):
                os.makedirs(directory)

            b.download_file(o.key, opath)
            print(o)

        try:
            b.delete()
        except Exception as e:
            print(e)

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

    def manutencao_buckets(self):

        self.s3_server = 'locaweb'
        self.s3_connect()

        # self.list_bucket()

        b = self.get_bucket('cmjatai_portal')

        for o in b.objects.all():
            print(o.last_modified, '{:.1f}MB'.format(
                o.size / 1024 / 1024), o.key)
            o.delete()
            continue

            """if '2021-0' in o.key or\
               '2021-1' in o.key or\
               '2021-2' in o.key or\
               '2021-3' in o.key or\
               '2021-6' in o.key:
                o.delete()"""
        b.delete()
        return

    def s3_size(self):

        size_global = 0
        count_global = 0
        count_uploaded = 0
        print('--------- S3 Size ---------')

        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                model_exec = False

                for f in m._meta.get_fields():
                    dua = f
                    # print(dua)
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

                size_model = 0
                count_model = 0
                count_model_uploaded = 0
                for i in m.objects.all().order_by('-id').values_list('metadata', flat=True):

                    metadata = i

                    if not metadata:
                        continue

                    count_global += 1
                    count_model += 1

                    if self.s3_server not in metadata:
                        continue

                    for fn in m.FIELDFILE_NAME:

                        if fn not in metadata[self.s3_server]:
                            continue

                        s = 0
                        if 'original_size' in metadata[self.s3_server][fn] and metadata[self.s3_server][fn]['original_size']:
                            s += metadata[self.s3_server][fn]['original_size']

                        if 'size' in metadata[self.s3_server][fn] and metadata[self.s3_server][fn]['size']:
                            s += metadata[self.s3_server][fn]['size']

                        if s:
                            count_uploaded += 1
                            count_model_uploaded += 1

                        size_global += s
                        size_model += s

                print(m, count_model, count_model_uploaded, size_model)

        print(
            f'S3 Server: {self.s3_server}. Itens Totais: {count_global}. Itens com cópia: {count_uploaded} Size: {size_global}')
