import logging
import os.path

from celery_haystack.indexes import CelerySearchIndex
from django.conf import settings
from django.db.models import F, Q, Value
from django.db.models.fields import TextField
from django.db.models.functions import Concat
from django.template import loader
from haystack import connections
from haystack.constants import Indexable
from haystack.fields import CharField, DateTimeField, IntegerField
from haystack.utils import get_model_ct_tuple
import magic

from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_PUBLIC, Dispositivo)
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.settings import SOLR_URL


class TextExtractField(CharField):

    backend = None
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.model_attr

        if not isinstance(self.model_attr, (list, tuple)):
            self.model_attr = (self.model_attr, )

    def solr_extraction(self, arquivo):
        if not self.backend:
            # connections['default'].get_backend()
            self.backend = self.search_index.get_backend()
        try:
            with open(arquivo.path, 'rb') as f:
                content = self.backend.extract_file_contents(f)
                data = ''
                if content:
                    # update from Solr 7.5 to 8.9
                    if content['contents']:
                        data += content['contents']
                    if content['file']:
                        data += content['file']
        except Exception as e:
            print('erro processando arquivo: ' % arquivo.path)
            self.logger.error(arquivo.path)
            self.logger.error('erro processando arquivo: ' % arquivo.path)
            data = ''
        return data

    def print_error(self, arquivo, error):
        msg = 'Erro inesperado processando arquivo %s erro: %s' % (
            arquivo.path, error)
        print(msg, error)
        self.logger.error(msg, error)

    def file_extractor(self, arquivo):
        # if settings.DEBUG or not os.path.exists(arquivo.path) or \
        #        not os.path.splitext(arquivo.path)[1][:1]:
        #    return ''

        try:
            if not arquivo or arquivo and not arquivo.name:
                return ''

            ext = arquivo.name.split('.')[-1]
            #mime = magic.from_file(arquivo.path, mime=True)

            if ext in ('zip', 'gz', 'tar', 'mp3', 'mp4', 'mpeg', 'jpeg', 'png'):
                return ''

            # manter limite maximo alinhado ao commando ocrmypdf
            if arquivo.size > 40 * 1024 * 1024:
                return ''

            if SOLR_URL:
                return self.solr_extraction(arquivo)
        except Exception as err:
            print(str(err))
            self.print_error(arquivo, err)
        return ''

    def ta_extractor(self, value):

        # if settings.DEBUG:
        #    return ''

        r = []
        for ta in value.filter(privacidade__in=[
                STATUS_TA_PUBLIC,
                STATUS_TA_IMMUTABLE_PUBLIC]):
            dispositivos = Dispositivo.objects.filter(
                Q(ta=ta) | Q(ta_publicado=ta)
            ).order_by(
                'ordem'
            ).annotate(
                rotulo_texto=Concat(
                    F('rotulo'), Value(' '), F('texto'),
                    output_field=TextField(),
                )
            ).values_list(
                'rotulo_texto', flat=True)
            r += list(filter(lambda x: x.strip(), dispositivos))
        return ' '.join(r)

    def string_extractor(self, value):
        return value

    def list_string_extractor(self, value):
        return '\n'.join(map(str, value.all()))

    def extract_data(self, obj):

        data = ''

        for attr, func in self.model_attr:
            if not hasattr(obj, attr) or not hasattr(self, func):
                raise Exception

            value = getattr(obj, attr)
            if not value:
                continue

            # if callable(value):
            if type(value) is type(self.extract_data):
                data_attr = getattr(self, func)(value()) + '  '
            else:
                data_attr = getattr(self, func)(value) + '  '

            data += data_attr

            if func == 'ta_extractor':
                data_attr = data_attr.strip()
                if data_attr:
                    break

        data = data.replace('\n', ' ')

        return data

    def prepare_template(self, obj):
        app_label, model_name = get_model_ct_tuple(obj)
        template_names = ['search/indexes/%s/%s_%s.txt' %
                          (app_label, model_name, self.instance_name)]

        t = loader.select_template(template_names)

        return t.render({'object': obj,
                         'extracted': self.extract_data(obj)})


class DocumentoAcessorioIndex(CelerySearchIndex, Indexable):
    model = DocumentoAcessorio
    data = DateTimeField(model_attr='data', null=True)
    ano = IntegerField(model_attr='ano')

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('autor', 'string_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('arquivo', 'file_extractor'),
        )
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_updated_field(self):
        return 'data_ultima_atualizacao'


class NormaJuridicaIndex(DocumentoAcessorioIndex):
    model = NormaJuridica
    data = DateTimeField(model_attr='data', null=True)
    tipo = CharField(model_attr='tipo__sigla')
    ano = IntegerField(model_attr='ano')
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('epigrafe', 'string_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('observacao', 'string_extractor'),
            ('texto_articulado', 'ta_extractor'),
            ('texto_integral', 'file_extractor'),
        )
    )


class MateriaLegislativaIndex(DocumentoAcessorioIndex):
    model = MateriaLegislativa
    tipo = CharField(model_attr='tipo__sigla')
    ano = IntegerField(model_attr='ano')
    data = DateTimeField(model_attr='data_apresentacao')
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('epigrafe', 'string_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('observacao', 'string_extractor'),
            ('autores', 'list_string_extractor'),
            ('texto_articulado', 'ta_extractor'),
            ('texto_original', 'file_extractor'),
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
