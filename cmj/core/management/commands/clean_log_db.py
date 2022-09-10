from datetime import timedelta
import logging

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
from django_celery_results.models import TaskResult

from cmj.core.models import AuditLog
from cmj.utils import Manutencao


class Array(Subquery):
    template = 'ARRAY(%(subquery)s)'


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()

        post_save.disconnect(dispatch_uid='timerefresh_post_signal')



        self.logger = logging.getLogger(__name__)

        self.clean_task_result()
        self.clean_blank_audit_log()

        self.count_registers(full=False)

    def count_registers(self, full=True):

        print('--------- CountRegisters ----------')

        for app in apps.get_app_configs():
            for m in app.get_models():
                count = m.objects.all().count()
                if full or count > 10000:
                    print(count, m, app)

        tr = TaskResult.objects.all().count()
        print(tr, TaskResult)

    def clean_task_result(self):
        data = timezone.localtime() - timedelta(days=5)
        TaskResult.objects.filter(
            date_done__lt=data).order_by('-date_done').delete()

    def clean_blank_audit_log(self):

        logs = AuditLog.objects.filter(
            email__exact='',
            content_type=OuterRef('content_type_id'),
            obj_id=OuterRef('obj_id')
        ).order_by('-id')

        group_logs = AuditLog.objects.filter(
            email__exact=''
        ).annotate(
            objs=Array(logs.values('id'))
        ).values(
            'content_type_id', 'obj_id', 'objs'
        ).distinct(
            'content_type_id', 'obj_id'
        ).order_by(
            'content_type_id', '-obj_id'
        )

        blank_len = 2

        logs_a_deletar = []
        for gl in group_logs:
            logs_a_deletar += gl['objs'][blank_len:]

        for i in range(0, len(logs_a_deletar), 1000):
            chunk = logs_a_deletar[i:i + 1000]

            dd = AuditLog.objects.filter(id__in=chunk)
            dd.delete()

    def clean_audit_log__old_v1(self):

        blank_len = 2

        group_logs = AuditLog.objects.filter(
            email=''
        ).values(
            'content_type_id', 'obj_id'
        ).annotate(
            count_tipos_obj=Count('obj_id')
        ).filter(
            count_tipos_obj__gt=blank_len
        ).order_by('content_type_id', '-obj_id')

        # print(group_logs.query)
        # print(group_logs.count())

        logs_a_deletar = []
        for gl in group_logs:  # [:10000]:

            if gl['content_type_id']:
                ct = ContentType.objects.get(pk=gl['content_type_id'])
            else:
                ct = None

            print(gl, ct)

            logs = AuditLog.objects.filter(
                email='',
                content_type=ct,
                obj_id=gl['obj_id']
            ).order_by('-id')

            logs_a_deletar += list(logs[blank_len:].values_list('id', flat=True))

            # print(logs.count())
            # print(logs.values_list('id', flat=True))

        for i in range(0, len(logs_a_deletar), 1000):
            chunk = logs_a_deletar[i:i + 1000]

            dd = AuditLog.objects.filter(id__in=chunk)
            dd.delete()
