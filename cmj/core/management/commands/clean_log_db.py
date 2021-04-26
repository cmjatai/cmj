from datetime import timedelta
import logging

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
from django_celery_results.models import TaskResult

from cmj.signals import Manutencao


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.clean_task_result()

        self.count_registers(full=False)

    def count_registers(self, full=True):

        print('--------- CountRegisters ----------')

        for app in apps.get_app_configs():
            for m in app.get_models():
                count = m.objects.all().count()
                if full or count > 10000:
                    print(count, m, app)

    def clean_task_result(self):
        data = timezone.localtime() - timedelta(days=5)
        objs = TaskResult.objects.filter(
            date_done__lt=data).order_by('-date_done').delete()
