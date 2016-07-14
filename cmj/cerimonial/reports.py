
from django.db.models import Q

from cmj.cerimonial.forms import ImpressoEnderecamentoContatoForm
from cmj.cerimonial.models import Contato
from cmj.globalrules.crud_custom import DetailMasterCrud
from cmj.utils import normalize


class ImpressoEnderecamentoContatoView(DetailMasterCrud.BaseMixin,
                                       DetailMasterCrud.ListView):
    permission_required = ('cerimonial.print_impressoenderecamento',)
    form_search_class = ImpressoEnderecamentoContatoForm
    model = Contato
    template_name = "crud/list.html"
    list_field_names = ['nome', 'data_nascimento']
    container_field = 'workspace__operadores'
