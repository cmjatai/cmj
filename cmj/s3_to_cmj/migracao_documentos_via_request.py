import mimetypes
import os
from time import sleep

from django.core.files.base import File
from django.core.files.temp import NamedTemporaryFile
from sapl.base.models import CasaLegislativa
from sapl.materia.models import (DocumentoAcessorio, MateriaLegislativa,
                                 Proposicao)
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (DocumentoAcessorioAdministrativo,
                                      DocumentoAdministrativo)
from sapl.sessao.models import SessaoPlenaria
import urllib3

from cmj.settings import MEDIA_ROOT


# MIGRAÇÃO DE DOCUMENTOS  ###################################################
EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/xml': '.xml',
    'text/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'text/html': '.html',
    'image/gif': '.gif',
    'text/rtf': '.rtf',
    'text/x-python': '.py',
    'text/plain': '.ksh',
    'text/plain': '.c',
    'text/plain': '.h',
    'text/plain': '.txt',
    'text/plain': '.bat',
    'text/plain': '.pl',
    'text/plain': '.asc',
    'text/plain': '.text',
    'text/plain': '.pot',
    'text/plain': '.brf',
    'text/plain': '.srt',
    'image/tiff': '.tiff',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
}

DOCS = {
    CasaLegislativa: [(
        'logotipo',
        'props_sapl/logo_casa.gif',
        'casa/logotipo/logo_casa.gif')],
    Parlamentar: [(
        'fotografia',
        'parlamentar/fotos/{}_foto_parlamentar',
        'public/parlamentar/{0}/{0}_foto_parlamentar{1}')],
    MateriaLegislativa: [(
        'texto_original',
        'materia/{}_texto_integral',
        'public/materialegislativa/{2}/{0}/{0}_texto_integral{1}')],
    DocumentoAcessorio: [(
        'arquivo',
        'materia/{}',
        'public/documentoacessorio/{2}/{0}/{0}{1}')],
    NormaJuridica: [(
        'texto_integral',
        'norma_juridica/{}_texto_integral',
        'public/normajuridica/{2}/{0}/{0}_texto_integral{1}')],
    SessaoPlenaria: [
        ('upload_ata',
         'ata_sessao/{}_ata_sessao',
         'public/sessaoplenaria/{0}/ata/{0}_ata_sessao{1}'),
        ('upload_anexo',
         'anexo_sessao/{}_texto_anexado',
         'public/sessaoplenaria/{0}/anexo/{0}_texto_anexado{1}')
    ],
    Proposicao: [(
        'texto_original',
        'proposicao/{}',
        'private/proposicao/{0}/{0}{1}')],
    DocumentoAdministrativo: [(
        'texto_integral',
        'administrativo/{}_texto_integral',
        'private/documentoadministrativo/{0}/{0}_texto_integral{1}')
    ],
    DocumentoAcessorioAdministrativo: [(
        'arquivo',
        'administrativo/{}',
        'private/documentoacessorioadministrativo/{0}/'
        '{0}_acessorio_administrativo{1}')
    ],
}

DOCS = {model: [(campo,
                 os.path.join('sapl_documentos', origem),
                 os.path.join('sapl', destino))
                for campo, origem, destino in campos]
        for model, campos in DOCS.items()}


def em_media(caminho):
    return os.path.join(MEDIA_ROOT, caminho)


def mover_documento(origem, destino):
    origem, destino = [em_media(c) if not os.path.isabs(c) else c
                       for c in (origem, destino)]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    os.rename(origem, destino)


def get_extensao(mime):
    try:
        return EXTENSOES[mime]
    except KeyError as e:
        raise Exception('\n'.join([
            'mimetype:',
            mime,
            ' Algumas possibilidades são:', ] +
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)] +
            ['Atualize o código do dicionário EXTENSOES!']
        )) from e


http = urllib3.PoolManager()


def migrar_docs_por_ids(model, sync=None, check=False):

    erros = []
    for campo, base_origem, base_destino in DOCS[model]:
        print('#### Migrando {} de {} ####'.format(campo, model.__name__))

        registros = model.objects.all().order_by('-id')

        if sync:
            registros = registros[:int(registros.count() * sync) + 1]

        for item in registros:

            campo_file = getattr(item, campo)
            if campo_file:
                print('PULANDO', item.id,  model._meta.object_name)
                continue
            # campo_file.delete()
            # sleep(5)

            """if check:
                for mime, ext in EXTENSOES.items():
                    filepath = base_destino.format()
                
                continue"""

            url = ('http://187.6.249.156:8480/sapl/%s'
                   ) % base_origem.format(item.pk)

            request = http.request('GET', url)

            try:
                data = request.data.decode('utf-8')
                print(item.pk, "Sem arquivo ou outro erro...")
            except:
                temp = NamedTemporaryFile(delete=True)
                temp.write(request.data)
                temp.flush()

                ct = request.getheaders()['Content-Type']
                print(item.pk, ct, campo, item)

                try:
                    name_file = '%s_%s%s' % (campo, item.id, get_extensao(ct))
                    campo_file.save(name_file, File(temp), save=True)
                except Exception as e:
                    erros.append(e)
    return erros


def migrar_documentos():
    for model in [
        Parlamentar,
        MateriaLegislativa,
        DocumentoAcessorio,
        NormaJuridica,
        DocumentoAdministrativo,
        DocumentoAcessorioAdministrativo,
    ]:
        erros = migrar_docs_por_ids(model)

    for e in erros:
        print(e)


# %run 'sapl/legacy/migracao_documentos_via_request.py'
if __name__ == '__main__':
    migrar_documentos()
