import logging
import os

from PIL import Image
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_delete, post_save

from cmj.core.models import OcrMyPDF
from cmj.diarios.models import DiarioOficial
from cmj.signals import Manutencao
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo
from sapl.sessao.models import SessaoPlenaria


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

    def transforma_imagens_armazenadas_em_pdf(self):
        models = [
            {
                'model': MateriaLegislativa,
                'file_field': ('texto_original',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data_apresentacao',
                'years_priority': 0
            },
            {
                'model': DocumentoAdministrativo,
                'file_field': ('texto_integral',),
                'count': 0,
                'count_base': 9,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DocumentoAcessorioAdministrativo,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': NormaJuridica,
                'file_field': ('texto_integral',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DocumentoAcessorio,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': DiarioOficial,
                'file_field': ('arquivo',),
                'count': 0,
                'count_base': 2,
                'order_by': '-data',
                'years_priority': 0
            },
            {
                'model': SessaoPlenaria,
                'file_field': ('upload_pauta', 'upload_ata', 'upload_anexo'),
                'count': 0,
                'count_base': 2,
                'order_by': '-data_inicio',
                'years_priority': 0
            },

        ]

        for md in models:

            m = md['model']

            q = Q()
            for f in md['file_field']:
                param = {f'{f}__iendswith': '.jpeg'}
                q |= Q(**param)
                param = {f'{f}__iendswith': '.jpg'}
                q |= Q(**param)
                param = {f'{f}__iendswith': '.png'}
                q |= Q(**param)

            qs = m.objects.filter(q)

            ct = ContentType.objects.get_for_model(m)
            for i in qs:
                if not OcrMyPDF.objects.filter(content_type=ct, object_id=i.id).exists():
                    OcrMyPDF.objects.filter(
                        content_type=ct, object_id=i.id).delete()

                for f in md['file_field']:
                    p = getattr(i, f)
                    if p:
                        print(i.id, f, p.path)

                        inn = p.path.replace(
                            'media/sapl/', 'media/original__sapl/')
                        inn = inn.replace('media/cmj/', 'media/original__cmj/')

                        out = inn.split('.')
                        out[-1] = 'pdf'
                        out = '.'.join(out)

                        temp_out = f'/tmp/{out.split("/")[-1]}'

                        img = Image.open(inn)
                        try:
                            dx, dy = img.info['dpi']
                        except:
                            dx, dy = 100, 100

                        img.convert('RGB')
                        img.save(temp_out, resolution=dx)

                        destino = os.path.basename(temp_out)

                        with open(temp_out, 'rb') as f_in:
                            p.save(destino, File(f_in), save=True)

                        print(p.path)
                        print(p.original_path)
