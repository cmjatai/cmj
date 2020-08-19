from celery_haystack.signals import CelerySignalProcessor
from django.apps import apps
from django.db.models.signals import pre_init, post_init, pre_save,\
    post_save, pre_delete, post_delete, pre_migrate, post_migrate

from cmj.sigad.models import Documento


class CelerySignalProcessor(CelerySignalProcessor):

    def enqueue_save(self, sender, instance, **kwargs):
        action = 'update'
        if isinstance(instance, Documento):
            if instance.visibilidade != Documento.STATUS_PUBLIC:
                action = 'delete'

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)


class Manutencao():

    def desativa_signals(self, app_signal=None):

        disabled_signals = [
            pre_init, post_init,
            pre_save, post_save,
            pre_delete, post_delete,
            pre_migrate, post_migrate,
        ]

        for app in apps.get_app_configs():
            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                for s in disabled_signals:
                    rs = s._live_receivers(m)
                    if rs:
                        for r in rs:
                            if s.disconnect(receiver=r, sender=m):
                                print(m, s, r)

    def desativa_auto_now(self):
        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():

                for f in m._meta.get_fields():
                    dua = f
                    # print(dua)
                    if hasattr(dua, 'auto_now') and dua.auto_now:
                        print(m, 'desativando auto_now')
                        dua.auto_now = False
