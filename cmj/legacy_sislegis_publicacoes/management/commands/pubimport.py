from collections import OrderedDict
from copy import deepcopy
from datetime import timedelta

from time import sleep

from PIL import Image, ImageDraw
from PIL.ImageFont import truetype
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import urllib3

from cmj.diarios.models import TipoDeDiario, DiarioOficial
from cmj.legacy_sislegis_portal.models import Documento, Tipolei, Itemlei
from sapl.compilacao.models import Dispositivo, TextoArticulado,\
    TipoTextoArticulado, TipoDispositivo, STATUS_TA_EDITION
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run()
        self.reset_id_model(DocumentoAdministrativo)

    def reset_id_model(self, model):

        query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                    coalesce(max("id"), 1), max("id") IS NOT null) 
                    FROM "%(app_model_name)s";
                """ % {
            'app_model_name': _get_registration_key(model)
        }

        with connection.cursor() as cursor:
            cursor.execute(query)
            # get all the rows as a list
            rows = cursor.fetchall()
            print(rows)

    def run(self):

        q = Q(id__gte=28) | Q(id=27) | Q(id=5) | Q(id=4)
        tipos = Tipolei.objects.exclude(q).order_by('id')
