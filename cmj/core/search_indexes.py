from unicodedata import normalize

from haystack import indexes

from cmj.core.models import Trecho


class TrechoIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True)
    display = indexes.CharField(indexed=False)

    def get_model(self):
        return Trecho

    def index_queryset(self, using=None):
        # filter(municipio__nome='Jataí')
        return self.get_model().objects.filter(municipio__nome='Jataí')

    def prepare_text(self, obj):
        txt = str(obj)
        return txt + ' - ' + normalize(
            'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

    def prepare_display(self, obj):
        return str(obj)
