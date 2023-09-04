import csv

from django.core.management.base import BaseCommand
from django.db.models.fields import DateField
from django.utils import formats

from cmj.arq.models import Draft
from cmj.cerimonial.models import Endereco, Telefone, Contato
from cmj.core.models import AreaTrabalho


class Command(BaseCommand):

    def handle(self, *args, **options):
        drafts = Draft.objects.all()

        for d in drafts:
            print(d.id, f'{str(d.owner): <50}', d.created)
