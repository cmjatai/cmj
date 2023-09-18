import csv
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models.fields import DateField
from django.utils import formats, timezone

from cmj.arq.models import Draft
from cmj.cerimonial.models import Endereco, Telefone, Contato
from cmj.core.models import AreaTrabalho


class Command(BaseCommand):

    def handle(self, *args, **options):
        drafts = Draft.objects.all()

        data_clear = timezone.now() - timedelta(days=7)
        for d in drafts:
            if d.created < data_clear:
                d.delete()
                #print(d.id, f'{str(d.owner): <50}', d.created)
