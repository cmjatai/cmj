
"""
TODO: PENSAR SOBRE A BUSCA COM ENCAPSULAMENTO DAS ÁREAS DE TRABALHO
 
class ContatoIndex(indexes.ModelSearchIndex, indexes.Indexable):

    text = CharField(document=True, use_template=False)

    class Meta:
        model = Contato
        fields = ['nome', 'nome_social']

    def index_queryset(self, using=None):
        return Contato.objects.all()

    def prepare_text(self, obj):
        txt = str(obj)
        return txt + ' - ' + normalize(
            'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

    def prepare_nome(self, obj):
        txt = str(obj.nome)
        return txt + ' - ' + normalize(
            'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

    def prepare_nome_social(self, obj):
        txt = str(obj.nome_social)
        return txt + ' - ' + normalize(
            'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')
"""