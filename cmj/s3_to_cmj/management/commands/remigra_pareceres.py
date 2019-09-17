import os
import re

from cairosvg.path import path
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.signals import post_delete, post_save

from sapl.materia.models import DocumentoAcessorio, TipoDocumento
from sapl.protocoloadm.models import DocumentoAdministrativo


class Command(BaseCommand):
    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run()

    def run(self):

        pareceres = DocumentoAcessorio.objects.filter(
            Q(autor__icontains='leonardo') | Q(
                autor__icontains='renata') | Q(autor__icontains='silmar'),
            tipo_id=1,
        )

        print(pareceres.count())
        count = 0

        for p in pareceres:
            m = re.match('([^0-9]+)([0-9]+)/ ?([0-9]+)', p.nome)
            if m:
                if 'projeto' not in p.nome and 'Proj.' not in p.nome:
                    pass
                else:
                    continue

            else:
                continue

            count += 1
            print('migrando... ', p.id, p.nome)

            nome_split = m.groups()

            d = DocumentoAdministrativo.objects.filter(
                temp_migracao_doc_acessorio=p.id).first()

            d_outro = DocumentoAdministrativo.objects.filter(
                temp_migracao_doc_acessorio__isnull=True,
                ano=int(nome_split[-1]),
                numero=int(nome_split[-2]),
                tipo_id=150).first()

            if not d:
                d = DocumentoAdministrativo()
                d.temp_migracao_doc_acessorio = p.id
                d.materia = p.materia

            if d_outro:
                if d_outro.protocolo:
                    d.protocolo = d_outro.protocolo
                d_outro.delete()

            if d.materia.autores.exists():
                d.interessado = ', '.join(map(str, d.materia.autores.all()))

            d.tipo_id = 150
            d.ano = int(nome_split[-1])
            d.numero = int(nome_split[-2])
            d.data = p.data
            d.assunto = p.ementa
            d.obervacao = p.indexacao
            d.workspace_id = 21
            d.save()

            if p.arquivo:

                if d.texto_integral:
                    d.texto_integral.delete()

                path = p.arquivo.path.replace('sapl', 'original__sapl')
                ext = os.path.basename(path).rsplit('.')[-1]

                with open(path, 'rb') as f:
                    d.texto_integral = File(
                        f,
                        'docadm_%s.%s' % (d.id, ext))

                    print(path)
                    print(d.texto_integral.path)
                    d.save()

                    print(p.arquivo.path)
                    print(d.texto_integral.path)

            p.delete()

        print(count)
