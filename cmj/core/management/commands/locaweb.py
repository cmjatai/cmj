

import logging

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
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

        print('--------- Locaweb ----------')
        for app in apps.get_app_configs():
            for model in app.get_models():

                if not hasattr(model, 'FIELDFILE_NAME') or \
                        not hasattr(model, 'metadata'):
                    continue

                print(model)
