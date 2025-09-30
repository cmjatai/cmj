
from ast import In
from django.utils.translation import gettext_lazy as _
from cmj.painelset.forms import EventoForm
from cmj.painelset.models import Evento, Individuo, ParteEvento
from sapl.crud.base import Crud, MasterDetailCrud


class EventoCrud(Crud):
    model = Evento

    class CreateView(Crud.CreateView):
        form_class = EventoForm
        layout_key = None

    class UpdateView(Crud.UpdateView):
        form_class = EventoForm
        layout_key = None


class IndividuoCrud(MasterDetailCrud):
    model = Individuo
    parent_field = 'evento'

    class ListView(MasterDetailCrud.ListView):
        paginate_by = 100

        def hook_name(self, obj, default, url):
            return '<a href="{}" pk="{}">{}</a>'.format(
                url, obj.id, obj.name), ''


class ParteEventoCrud(MasterDetailCrud):
    model = ParteEvento
    parent_field = 'evento'