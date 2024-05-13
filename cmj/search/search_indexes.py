import logging

from celery_haystack.indexes import CelerySearchIndex
from django.db.models import F, Q, Value
from django.db.models.fields import TextField
from django.db.models.functions import Concat
from django.template import loader
from haystack.constants import Indexable
from haystack.fields import CharField, DateTimeField, IntegerField, BooleanField,\
    MultiValueField

from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import Documento
from sapl.compilacao.models import (STATUS_TA_IMMUTABLE_PUBLIC,
                                    STATUS_TA_PUBLIC, Dispositivo)
from sapl.materia.models import DocumentoAcessorio, MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria
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
        return ''
        try:
            if not arquivo or arquivo and not arquivo.name:
                return ''

            ext = arquivo.name.split('.')[-1]
            #mime = magic.from_file(arquivo.path, mime=True)

            if ext in ('zip', 'gz', 'tar', 'mp3', 'mp4', 'mpeg', 'jpeg', 'png'):
                return ''

            # manter limite maximo alinhado ao commando ocrmypdf
            # if arquivo.size > 40 * 1024 * 1024:
            #    return ''

            self.logger.debug(
                f'Extraindo arquivo: {arquivo.name} - tamanho: {(arquivo.size/1024/1024):.5}MB')
            if SOLR_URL:
                dados_extraidos = self.solr_extraction(arquivo)
                self.logger.debug(
                    f'Tamanho dos Dados Extraídos: {(len(dados_extraidos)/1024/1024):.5}MB')
                return dados_extraidos
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

            # if func == 'ta_extractor':
            #    data_attr = data_attr.strip()
            #    if data_attr:
            #        break

        data = data.replace('\n', ' ')

        return data

    def prepare_template(self, obj):
        #app_label, model_name = get_model_ct_tuple(obj)
        template_names = ['search/indexes/default_text.txt']
        # template_names = ['search/indexes/%s/%s_%s.txt' %
        #                  (app_label, model_name, self.instance_name)]

        t = loader.select_template(template_names)

        return t.render({'object': obj,
                         'extracted': self.extract_data(obj)})


class SigadTextExtractField(TextExtractField):

    def __init__(self, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)

    def extract_data(self, obj):

        data = ''
        ds = (obj.titulo, obj.descricao, obj.autor, obj.texto)
        data += ' '.join(filter(None, ds))

        for child in obj.childs.all():
            data += self.extract_data(child)

        data = data.replace('\n', ' ')
        return data


class BaseIndex:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def get_updated_field(self):
        return 'data_ultima_atualizacao'


class DiarioOficialIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = DiarioOficial

    ano_i = IntegerField(model_attr='ano')
    data_dt = DateTimeField(model_attr='data', null=True)
    tipo_i = IntegerField(model_attr='tipo_id')

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('descricao', 'string_extractor'),
            ('arquivo', 'file_extractor'),
        )
    )


class NormaJuridicaIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = NormaJuridica

    pk_i = IntegerField(model_attr='pk')

    ano_i = IntegerField(model_attr='ano')
    numero_s = CharField(model_attr='numero')
    data_dt = DateTimeField(model_attr='data', null=True)
    tipo_i = IntegerField(model_attr='tipo_id')

    assuntos_is = MultiValueField(
        model_attr='assuntos__id', null=True)

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

    def prepare_numero_s(self, obj):
        return f'{obj.numero:>06}'


class DocumentoAcessorioIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = DocumentoAcessorio

    ano_i = IntegerField(model_attr='ano')
    data_dt = DateTimeField(model_attr='data', null=True)
    tipo_i = IntegerField(model_attr='tipo_id')

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('autor', 'string_extractor'),
            ('ementa', 'string_extractor'),
            ('indexacao', 'string_extractor'),
            ('arquivo', 'file_extractor'),
        )
    )


class MateriaLegislativaIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = MateriaLegislativa

    pk_i = IntegerField(model_attr='pk')

    em_tramitacao_b = BooleanField(model_attr='em_tramitacao')
    tipo_i = IntegerField(model_attr='tipo_id')
    ano_i = IntegerField(model_attr='ano')
    numero_i = CharField(model_attr='numero')
    data_dt = DateTimeField(model_attr='data_apresentacao')

    uta_i = IntegerField(
        model_attr='ultima_tramitacao__unidade_tramitacao_destino_id', null=True)

    sta_i = IntegerField(
        model_attr='ultima_tramitacao__status_id', null=True)

    autoria_is = MultiValueField(
        model_attr='autores__id', null=True)

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

    def index_queryset(self, using=None):

        qs = self.get_model()._default_manager.all()

        # return qs
        # prefetch_related
        return qs.select_related(
            "tipo",
        ).prefetch_related(
            "autoria_set",
            "autoria_set__autor",
            "anexadas",
            "tramitacao_set",
            "tramitacao_set__status",
            #"tramitacao_set__unidade_tramitacao_local",
            "tramitacao_set__unidade_tramitacao_destino",
            "normajuridica_set",
            "normajuridica_set__tipo",
            "registrovotacao_set",
            "registrovotacao_set__ordem__sessao_plenaria",
            "registrovotacao_set__ordem__sessao_plenaria__tipo",
            "documentoacessorio_set")


class SessaoPlenariaIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = SessaoPlenaria

    ano_i = IntegerField(model_attr='ano')
    data_dt = DateTimeField(model_attr='data_inicio', null=True)
    tipo_i = IntegerField(model_attr='tipo_id')
    sessao_legislativa_i = IntegerField(model_attr='sessao_legislativa_id')
    legislatura_i = IntegerField(model_attr='legislatura_id')

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('__str__', 'string_extractor'),
            ('upload_ata', 'file_extractor'),
            ('upload_pauta', 'file_extractor'),
            ('upload_anexo', 'file_extractor'),
        )
    )


class DocumentoAdministrativoIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = DocumentoAdministrativo

    ano_i = IntegerField(model_attr='ano', null=True)
    data_dt = DateTimeField(model_attr='data', null=True)
    at = IntegerField(model_attr='workspace_id', null=True)

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('__str__', 'string_extractor'),
            ('texto_integral', 'file_extractor'),
            ('assunto', 'string_extractor'),
            ('observacao', 'string_extractor'),
        )
    )


class DocumentoIndex(BaseIndex, CelerySearchIndex, Indexable):
    model = Documento

    ano_i = IntegerField(model_attr='ano')
    data_dt = DateTimeField(model_attr='public_date')

    text = SigadTextExtractField(
        document=True, use_template=True
    )

    def index_queryset(self, using=None):
        qs = self.get_model().objects.public_all_docs()
        return qs

    def get_updated_field(self):
        return 'created'

    def should_update(self, instance):
        return instance.raiz is None
