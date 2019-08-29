from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import CharField, DateField, DateTimeField

from cmj.sigad.models import Documento
from sapl.base.search_indexes import TextExtractField


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


class DocumentoIndex(CelerySearchIndex, Indexable):
    model = Documento
    data = DateTimeField(model_attr='public_date')
    text = SigadTextExtractField(
        document=True, use_template=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        qs = self.get_model().objects.public_all_docs()
        return qs

    def get_updated_field(self):
        return 'modified'

    def should_update(self, instance):
        return instance.raiz is None
